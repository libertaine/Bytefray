# Bytefray V6 E4 — Mirrored Pass Order: Research Tooling, Pre-registration and Experiment Freeze

**Status:** The E4 research tooling is built and qualified. The experiment is frozen, and both controls (C-E4, C-E4K1) have been run and qualified. **Neither treatment condition (T-E4, T-E4K1) has been run.** Nothing in this record is a gameplay result, and no E4 conclusion is drawn.
**Branch:** `v6-research`. Baseline `13cbd371d4c8921a260a58e97e4e9eff12ca6b63`; tooling qualified at `108d08d358611c073731ae1b1020b91da8c907fb`; analysis freeze committed at `e0d39b3560477e21ac619e2fd26130e25938c798`; control qualification committed at `6815cab7806f85d88939788ad85aeb91a913b8ee`.
**Authority:** [`V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md`](V6_E4_ORDER_VS_EVALUATION_TIMING_DESIGN_REVIEW.md), preserved verbatim at `b4d6024` (SHA-256 `5d9290c0cf5ebbd85d80956e504f9cd3f1f7e1e1ef9a811dae7e2fec87990cc0`): §D.1 source roles; §M prospective metrics; §N populations, hypotheses and interpretation; §O matrix; §P evidence rules; §Q historical-control reuse; §R qualification, freeze and hard stops. The Rulesets are recorded in [`V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md`](V6_E4_MIRRORED_PASS_ORDER_REGISTRATION.md) and are unchanged by this phase.

## Scope

This phase carries out the review's §R steps 4 to 8:

- it builds the research tooling: an E4 analyzer, the a-priori contest-class table and the gates;
- it freezes the pre-registration, the matrix identity and, separately, the analysis identity;
- it runs the two controls and passes them through the parent reproduction gate;
- it qualifies the tooling on control data only, freezes the control populations, and runs the G.4′ manipulation gate and the D9′ real-fixture gate.

It stops before §R step 9. The treatment is separately authorized and was not run.

No gameplay code changed. `engine/src` is byte-identical to the qualified E4 implementation (tree `940a27bcf8c62268eb15210cc30c28cae4d33e50`, commit `107e077`) at every commit of this phase. `scheduler_pass_order`, the mirrored pass semantics, E3 disruption, capture hold, scoring, rotation, quota, process selection and the replay and result schemas are untouched. Capture analyzer v2, E3 action/parity analyzer v1 and every other reused E2 and E3 module are reused byte for byte, by import, and are pinned.

## Where things live

| Path | Contents |
|---|---|
| `tools/research/v6/e4/cell_metrics.py` | Per-cell FMA and FPS (version 1), with cross-checks against the reused analyzers |
| `tools/research/v6/e4/telemetry.py` | Per-cell telemetry for a whole corpus: E3 action/parity analyzer v1 (and through it capture analyzer v2) plus the E4 cell metrics; process pool, JSONL, repeatability digests |
| `tools/research/v6/e4/analyze_e4.py` | E4 analyzer v1: units, unit medians and bands, transition classes, the matchup census, P-PAR, seat metrics, mirror claims, and the E4-H0–H8 and D9′ criteria and interpretation |
| `tools/research/v6/e4/contest_classes.py` / `contest_classes.json` | The §D.1 source-role table and the frozen contest classes |
| `tools/research/v6/e4/matrix.py` | The frozen experiment definition and its digest |
| `tools/research/v6/e4/preregistration.json` / `preregistration.py` | E4-H0–H8, D9′ and the rules around them, verbatim, plus the operationalizations; digest pinned |
| `tools/research/v6/e4/gates.py` | Parent reproduction, E3 continuity, orientation-aware integrity, the relabel gate, the G.4′ manipulation checks and the D9′ stop |
| `tools/research/v6/e4/populations.py` / `control_populations.json` | The frozen control populations and baseline |
| `tools/research/v6/e4/manipulation_gate.py` | The G.4′ gate: runtime offer sequence, exhaustive jam bound, fixture checks |
| `tools/research/v6/e4/d9_gate.py` | The D9′ real-fixture gate |
| `tools/research/v6/e4/analysis_freeze.py` / `analysis_freeze.json` | The analysis freeze identity and its committed record |
| `tools/research/v6/e4/run_e4.py` | The runner: `plan`, `execute`, `telemetry`, `reproduce`, `qualify`, `populations`, `manipulation`, `d9`, `unlock`, and, for after authorization, `treatment-telemetry`, `treatment-gates` and `analyze` |

No new fixture was added. E4 reuses the E2 fixtures and twins and E3's `e3_jam_sniper` and its twin, from tracked sources.

## The E4 analyzer

**Cell metrics** (`cell_metrics.cell_metrics`) read one canonical replay and its `result.json`. They rebuild per-tick core ownership exactly as E3 PM-1 does. On every replay they require agreement with the reused analyzers: E3 PM-1's swing ticks, first-mover-favouring swings and both-alive ticks per parity, and capture analyzer v2's final owned cells and its zero-core evaluations split by who moved first. Any difference is counted as a reconstruction disagreement.

| Metric | Definition (operationalization) |
|---|---|
| **FMA** | b(t) = Seat A's owned own-core cells − Seat B's at the end of tick t, over ticks where both entrants are alive. FMA = ½ (mean b over A-first ticks − mean b over B-first ticks), an exact rational in [−8, 8]. A-first ticks are those with (t − 1) mod 2 = 0. FMA is defined with zero swings. With fewer than 10 both-alive ticks of either parity the cell is `DECIDED_EARLY`, counted and never dropped (O-FMA-CELL). |
| **FMA bands** | strong-first ≥ 1.5; moderate-first 0.5 ≤ FMA < 1.5; neutral \|FMA\| < 0.5; moderate-last −1.5 < FMA ≤ −0.5; strong-last ≤ −1.5, on the exact value (O-FMA-BAND) |
| **PM-1** | FMS, PD, direction and `NOT_SCOREABLE`, retained unchanged from E3 action/parity analyzer v1. `NOT_SCOREABLE` is never converted into neutral. |
| **FPS** | The share of swing ticks that favour the tick's final-chunk owner. The owner is read from the Ruleset registry: the replay's Ruleset policy runs its own scheduler for that tick with both entrants live, and the last offer's entrant owns the final chunk. Scored with ≥ 10 swings. The identities FPS = 1 − FMS (forward) and FPS = FMS (mirrored) are checked in every cell (O-FPS). |

The canonical trace (review §L-1, the sniper against the disrupt guard at seed 42, outside the matrix) gives exactly:

- **Forward order.** The guard's core alternates 7 and 3 while the sniper keeps 7. So b = 0 on A-first ticks and 4 on B-first ticks, FMA = −2 (strong-last), balance sums {0, 2000} over 500 + 500 both-alive ticks, 999 swings, FPS 1.
- **Mirrored order.** A static 7 v 5, FMA 0, one swing, FPS `NOT_SCOREABLE`, and a first-mover final-chunk owner.

**Analysis** (`analyze_e4`):

- **Units (O-UNIT).** A round-robin pairing gives two ordered matchups (field, Seat-A agent, Seat-B agent), each observed at seeds 1–32. A twin mirror is one unit whose observations are its seeds (the candidate-first cell). The duplicate orientation is used only by the relabel gate. The F4 jam mirror is a mirror unit inside F4. F2, F2-P and F4 are never pooled.
- **Unit median (O-MATCHUP-MEDIAN).** The exact median of the unit's defined cell FMAs. A unit is `DECIDED-EARLY` when fewer than half of its cells are defined.
- **Transition classes** (control band → treatment band) follow §M.2. They are listed under Operationalizations below.
- **The census** counts units (matchups), per contest class and overall. Each unit carries n_distinct, its number of distinct (C key, T key) transitions. Cell-weighted and distinct-weighted values are secondary.

## Seat metrics

Following §M.1 (O-SEAT-METRICS):

- **Round-robin pairings (F1; F4 reported separately).** For each seed, the XY cell puts X in Seat A and the YX cell puts Y there.
  - DSC(s) = 1 when both are won by the same seat. SDI is the mean of DSC.
  - EC(s) = 1 when both are won by the same entrant.
  - OS is the mean of 1[e_XY ≠ e_YX].
  - GSB = (#A − #B) / 2S.
  - p_A is the share of seat-consistent seeds won by A, and SB = \|2p_A − 1\|.
  - SDom = SDI · SB and SCD = SDI · (1 − SB). With no seat-consistent seed, p_A and SB are undefined and SDom = SCD = 0.
  - The legacy harness SDI, the mean over distinct seed-level trajectories, is reported unchanged beside it.
- **Twin mirrors.** The unit is the seed. The analyzer reports decisive share, GSB = (#A − #B) / S, p_A over decisive seeds, SB, SDom = decisive share · SB and SCD = decisive share · (1 − SB).
- **Mirror claims (O-MIRROR-CLAIM).** A claim is `seat_dominant` (with its seat) when SDom ≥ 0.9, `seed_conditioned` when SCD ≥ 0.5, and `not_seat_determined` otherwise. A claim that differs between 1000 ticks (F2) and 1001 ticks (F2-P) is `TICK_LIMIT_PARITY_DEPENDENT`.

The review's §M.1 worked example is reproduced exactly on the re-run control. The guarded-painter mirror under the T-E3 Ruleset (C-E4) has 32/32 decisive seeds, 19 A and 13 B, GSB = 3/16, SDom = 3/16 and SCD = 13/16.

## Contest classes

`contest_classes.json`, SHA-256 **`47097041e36189e4a92c837080055cacd40ab53c4203f699564550d6507f7969`**, is pinned in the matrix definition. It is derived from the §D.1 source roles alone, and `load_table` re-derives it on every load. No outcome, probe or control value enters it.

- **MULTI-PASS:** one side writes the other's non-base core cells, and the other repairs non-base core cells.
- **OPENING-ONLY:** no multi-pass contest, but one side writes the other's anchor (core cell 0) and the other repairs its base.
- **INCIDENTAL:** neither.
- A twin has its primary's roles.

**O-CONTEST-ROLES.** §D.1 gives `e2_repair_guard` no base-only repair. But its cyclic cursor writes every own core cell, cell 0 included, across ticks, and §D.2 files repair guard v guarded painter under OPENING-ONLY because of that. The repair guard is therefore read as repairing its base. This is the only role reading the table adds.

| Field | MULTI-PASS | OPENING-ONLY | INCIDENTAL |
|---|---|---|---|
| F1 (36 pairings) | 10: disrupt guard v min guard, v spread defender, v spread sniper; repair guard v min guard, v spread defender, v spread sniper; sniper v disrupt guard, v repair guard; probe v disrupt guard, v repair guard | 15 | 11 (every greedy-painter pairing, sniper v spread sniper, probe v sniper and v spread sniper) |
| F2 / F2-P (9 mirrors each) | 0 | 4: disrupt guard, guarded painter, min guard, spread defender | 5 |
| F4 (10 pairings, separate stratum) | 2: jam sniper v disrupt guard, v repair guard | 3 | 5 (including the jam mirror) |

## Frozen experiment definition

`matrix.py`, digest `fc29d575dd256777a9b18c1d076716677a89a6e4eac8943ec2cefc703ceff4ef`, **matrix id `v6-e4-matrix-v1-fc29d575dd25`**.

| Condition | Ruleset | K | λ | Pass order | Role |
|---|---|---|---|---|---|
| C-E4 | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1` | 2 | 1 | forward | Primary control; must reproduce historical T-E3 |
| T-E4 | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1-mirrored-passes` | 2 | 1 | mirrored | Primary treatment |
| C-E4K1 | `bytefray-rules-6-research-disruption-slot1` | 1 | 1 | forward | Companion control; must reproduce historical T-E3K1 |
| T-E4K1 | `bytefray-rules-6-research-disruption-slot1-mirrored-passes` | 1 | 1 | mirrored | Companion treatment |

On every load the registry is re-checked: each treatment must differ from its parent only in `scheduler_pass_order` (and its id).

| Field | Composition | Ticks | Orientations | Per condition |
|---|---|---|---|---|
| F1 | 9 agents (the E2 set **minus `e2_counter`**), triangular: 36 pairs × 32 seeds × 2 | 1000 | both | 2,304 |
| F2 | 9 twin mirrors × 32 × 2; the duplicate orientation serves only the relabel gate | 1000 | both | 576 |
| F2-P | 9 twin mirrors × 32 × 1 | 1001 | candidate-first only | 288 |
| F4 | `e3_jam_sniper` × 9 agents, plus the jam mirror, × 32 × 2 | 1000 | both | 640 |

- **Totals.** 3,808 per condition; the primary study (C-E4 + T-E4) is 7,616 matches, and the full experiment is **15,232**. The real evaluation planner's dry run plans exactly 15,232 cells, with every condition and field consistent in Ruleset, tick limit, seeds and orientations.
- **Fixed settings.** Arena 512; seeds 1–32, given explicitly; no K = 3 arm. All four request overrides (`scheduler_chunk_size`, `scheduler_rotate_start`, `kill_weight`, `instr_per_tick`) must be `None` on the exact requests that run; the runner fails closed otherwise.
- **Fingerprints.** The definition freezes the fingerprints of all 20 entrants: the 9 agents, their 9 twins, the jam sniper and its twin. These are the E2 and E3 frozen values.
- **Historical parents.** C-E4 must reproduce E3's T-E3 corpus and C-E4K1 E3's T-E3K1, in every field.

**Guards on every execution** (`run_e4.execute`), as in E3:

- an explicit `--confirm-matrix-execution`;
- the frozen matrix, contest-class and pre-registration digests, and the registry check;
- the committed analysis freeze, still holding against the live tooling;
- a clean tree whose `engine/src` is the frozen tree, and whose tooling files equal their content at the tooling commit, checked before and again after the run;
- live fingerprints equal to the frozen ones;
- request checks on the planned requests;
- the exact cell count;
- refusal to run a cell set whose output directory already exists;
- for every control, a STOP if any treatment artifact exists.

A treatment additionally needs `--confirm-treatment-execution` and the unlock chain.

## Hypothesis pre-registration

`preregistration.json`, SHA-256 **`56307844e1c01a52b46b3fc1d100a34706e13d6a645614d6d2bcea94757b9973`**, is pinned in `preregistration.py`, and loading fails closed on any change. It holds the following, verbatim from the review:

- E4-H0–H8 and D9′, with statement, supported-if and refuted-if clauses and probe prior;
- the populations and the §M metric definitions, including the transition classes;
- the interpretation table, with "A clean negative is reachable";
- the threshold rationale;
- the eight §P evidence rules;
- the twelve §R hard stops.

Only markdown emphasis, code formatting and pipe escapes are removed. `test_v6_e4_matrix.py` parses the preserved review and asserts each section equal to the file.

| ID | Statement | Supported if | Refuted if |
|---|---|---|---|
| E4-H0 | No structural effect | STAYS + UNCHANGED-NEUTRAL ≥ 0.90 of P-PAR, **and** H1 refuted | < 0.90 |
| E4-H1 | Response-order concentration is load-bearing | In MULTI-PASS P-PAR, NEUTRALIZED + WEAKENED ≥ 2/3, **and** overall FOLLOWS-FINAL ≤ 1/10 | NEUTRALIZED + WEAKENED ≤ 1/10 of MULTI-PASS |
| E4-H2 | Final pre-sample position is load-bearing: the privilege transfers | FOLLOWS-FINAL ≥ 2/3 of MULTI-PASS P-PAR | ≤ 1/10 |
| E4-H3 | Opening-pass response privilege | In OPENING-ONLY P-PAR, STAYS ≥ 2/3 | STAYS ≤ 1/10 |
| E4-H4 | Hold × order masking | Companion outcome-class change share in MULTI-PASS exposed F1 ≥ 0.10 while the primary's ≤ 0.02 | Companion ≤ 0.02 |
| E4-H5 | New early-capture pathology | Primary: ≥ 0.10 of control non-capture exposed F1 cells become captures | < 0.10 |
| E4-H6 | Stasis / draw-ification | Exposed-F1 tick-limit share rises ≥ 0.10 (flag); static neutralization reported | Rise < 0.10 |
| E4-H7 | Seed-conditioned seat dependence remains | \|GSB\| ≤ 0.10 in every unit, and ≥ 1 unit with SCD ≥ 0.5 at n_distinct ≥ 8 | No unit with SCD ≥ 0.5 |
| E4-H8 | Tick-limit parity artifact | Any mirror claim differs between 1000 and 1001 | All agree |
| D9′ | G.5′ immunity (theorem) | T-E4: 0 completions against repair and disrupt guards (and twins). Also a hard stop. | — |

| Result | Conclusion (pre-registered) |
|---|---|
| H1 ∧ H3 ∧ ¬H2 | Two order mechanisms: multi-pass response-order concentration, which order can remove, and the second mover's opening response, which it cannot. Next: anchor/core-0 co-location. |
| H1 ∧ ¬H3 ∧ ¬H2 | Response-order concentration causes the residual broadly |
| H2 | The privilege follows the final pre-sample chunk. Next: evaluation structure. |
| ¬H1 ∧ H3 | The residual is the opening-pass effect; the in-tick order line closes. Next: co-location. |
| H0 | Order is not load-bearing; the line closes |
| H5, H6, H8 | Recorded as pathologies whatever else holds |
| none | "No registered row applies" is itself the registered outcome |

**Operationalizations.** Each one fixes, before any treatment data exists, only what the review leaves open, and each is labelled in the file:

- the cell and band ones: O-FMA-CELL, O-FMA-BAND, O-FPS;
- the unit ones: O-UNIT, O-MATCHUP-MEDIAN;
- the populations and contest classes: O-P-PAR, O-P-STALE, O-CONTEST, O-CONTEST-ROLES;
- the cell-set ones: O-EXPOSED, O-OUTCOME-CLASS (E3's, unchanged), O-CAPTURE, O-H4-H6;
- the seat and mirror ones: O-SEAT-METRICS, O-MIRROR-CLAIM;
- the gates: O-D9-PRIME, O-G4-PRIME, O-RELABEL, O-CONTROL-CENSUS;
- the reading rules: O-STATUS, O-INTERPRETATION.

Three of them need stating here:

- **O-TRANSITION: an overlap in §M.2, resolved before any treatment data existed.** §M.2 defines NEUTRALIZED as "control non-neutral → treatment neutral" and WEAKENED/STRENGTHENED as "same side, band down/up". Both also cover a first-side control, while FIRST-SIDE-CONTROL is "control first-side (no discriminating prediction; reported)". So that the classes partition the units, they are assigned in this order:
  1. DECIDED-EARLY if the unit is decided early in either arm;
  2. FIRST-SIDE-CONTROL if the control band is first-side;
  3. for a neutral control: UNCHANGED-NEUTRAL if the treatment is neutral, else NEW;
  4. for a last-side control: NEUTRALIZED (treatment neutral), FOLLOWS-FINAL (treatment first-side), STAYS (same band), WEAKENED (the weaker last band) or STRENGTHENED (the stronger).

  No class is merged, and the §M.2 wording is otherwise unchanged. On the frozen control, no unit in either arm is first-side, and every P-PAR unit is last-side, so step 2 never applies to a P-PAR unit.
- **O-INTERPRETATION.** A row applies when every hypothesis it names has the required status: a plain one SUPPORTED, a negated one REFUTED. NEITHER and NOT_EVALUABLE satisfy neither. The pathology row applies when any of H5, H6 and H8 is SUPPORTED, and the "none" row when none of the five main rows applies. Several rows may apply, and all are reported. A D9′ STOP replaces the reading.
- **O-CONTROL-CENSUS.** Control against itself, only identity classes may occur: STAYS, UNCHANGED-NEUTRAL, FIRST-SIDE-CONTROL and DECIDED-EARLY. Any other class is an analyzer defect and a hard stop.

No threshold was derived from probe, corpus or control outcomes. The control numbers in this record were computed after the thresholds were frozen, and none of them sets or adjusts one.

## Statistical and evidence rules (implemented)

- **Unit.** The ordered matchup, summarized by its median over seeds; twin mirrors count once, with the seed as the unit.
- **Rate claims.** They need n_distinct ≥ 8. Below that the harness label is `deterministic_characterization` (1) or `limited_distinct_trajectories` (2–7), and `rate_claim_eligible` is false.
- **Census.** Population criteria are census counts of matchup characterizations, not medians of mixtures. Cell-weighted P-STALE summaries are reported for continuity only.
- **Parity.** Two-sided, with direction. `NOT_SCOREABLE` and `DECIDED_EARLY` are counted categories. Static neutralization is scored through FMA and never dropped.
- **Control against itself.** Every criterion is computed control against control, frozen before treatment, and must be 100% identity classes.
- **Mirrors.** Analyzed at the seed level; claims must agree at 1000 and 1001 ticks.
- **Strata and arms.** F4 is never pooled. The companion feeds H4 only and never replaces a primary verdict.
- **Bradley–Terry and residuals.** Dropped as criteria.

## Freeze identities

The two identities are kept apart.

| Identity | Value | Covers |
|---|---|---|
| Matrix | **`v6-e4-matrix-v1-fc29d575dd25`** (`fc29d575…c703ceff4ef`) | the four conditions, their Rulesets, K, λ and pass order; the fields, pairs, seeds, orientations and per-field tick limits; the arena; the 9-agent roster and the excluded `e2_counter`; the jam fixture; all 20 fingerprints; the forbidden overrides; the contest-class table's SHA-256; the historical parents; and the counts |
| Analysis freeze | **`v6-e4-freeze-v1-101a941f5e30`** (`101a941f…c8f87`) | the matrix id and digest; the pre-registration SHA-256; the contest-class SHA-256; E4 analyzer v1 (`analyze_e4.py` `c891abe0…f2ab1`) and cell metrics v1 (`cbfe6424…3e0b`); capture analyzer v2 (`b818f53e…2c18f86`, pinned to E2 freeze `v6-e2-freeze-v2-db6458596d82`); E3 action/parity analyzer v1 (`86b1a557…c4f211`); the SHA-256 of all 31 tooling files, including the reused E2 and E3 modules, fixtures and E3's `control_populations.json`; the tooling commit `108d08d…`; the match-generation tree `engine/src` = `940a27bc…`; the E4 parent freeze (`b144e1d`, 96 matches); and the E3 parent provenance |

On every load, each reused E3 file is checked against E3 freeze v1's pin, capture analyzer v2 against E2 freeze v2's pin, and E3's populations file against E3's pinned SHA-256.

**Historical provenance** (recorded, never renamed): E3 matrix `v6-e3-matrix-v1-634132ec3c15` (`634132ec…37215e8`), E3 freeze `v6-e3-freeze-v1-506811e78ad8`, generated at `6f0fd3f3fb7fc6203daba5b9e049b4a4e58e801e`, engine tree `67b73c9ae7d40209ef68e9512a58c5adfef0ac2f`.

The freeze record's `control_qualification` block lies outside the identity digest. It was added after the controls passed, and it pins the SHA-256 of the four control-phase gate records and of `control_populations.json`.

## Control execution

Both controls ran through `run_e4 execute CONDITION FIELD --confirm-matrix-execution --workers 1` at `e0d39b3` with a clean tree: all eight fields in parallel processes, one match worker each. Each field passed the execution-source check before and after its run. A source manifest was taken before the runs. It covered `HEAD`, the trees of `engine/src` and `tools/research/v6`, and the SHA-256 of every E4 tooling file, the reused E3 modules, capture analyzer v2 and the harness. It was identical after the runs, and the tree was clean.

| Condition | F1 | F2 | F2-P | F4 | Total | Wall clock (UTC) |
|---|---|---|---|---|---|---|
| C-E4 | 2,304 | 576 | 288 | 640 | 3,808 | 18:33:18–18:51:32 |
| C-E4K1 | 2,304 | 576 | 288 | 640 | 3,808 | 18:33:18–18:49:01 |

The artifacts are under `runs/research_v6_e4/v6-e4-matrix-v1-fc29d575dd25/{C-E4,C-E4K1}/{F1,F2,F2-P,F4}`, and every `result.json` and replay is preserved (git-ignored). No cell failed. **No T-E4 or T-E4K1 directory exists.**

**Aborted first attempt (incident).** A first launch at 18:31 UTC used six match workers per field.

- **What failed.** C-E4 F1 stopped after 31 seconds with `PermissionError: [WinError 5] Access is denied` on the harness's atomic replace of `.evaluation.json.<tmp>` over `evaluation.json`. This is a Windows file-system race between workers writing the same evaluation file. It is not a gameplay or tooling result.
- **Response.** The other runs of that attempt were stopped, and the partial output was moved out of the matrix root to `runs/research_v6_e4/_aborted_control_attempt_1_workers6/`: C-E4 F1 512 cells, C-E4 F2 507, C-E4K1 F1 1,116; no treatment data.
- **Relaunch.** All eight fields were relaunched from empty directories with one worker each, and nothing else was changed.
- **Determinism check.** Afterwards, all 2,135 partial cells were compared with the qualified corpus. Every replay (by SHA-256) and every `result.json` (minus `completed_at` and `occurrence_id`) is identical.
- **Status of the partial data.** The aborted data is not part of the corpus and is not analyzed.

## Parent reproduction gate

**FULL PASS** (`parent_reproduction.json`, SHA-256 `4ac13444eee8677fece973a507446e7ebdf04c27b319450a3630e6e53604e5c2`). Each new control and its historical parent run under the same Ruleset id, so nothing is excused. The comparison covers:

- every harness cell field, including `match_id` and `result_id`;
- the whole `result.json` apart from `completed_at` and `occurrence_id`, including winner, reason, ticks and score;
- the replay bytes, by SHA-256;
- the E3 telemetry (capture analyzer v2 and the action/parity record);
- the E4 FMA and FPS metrics, computed on both copies.

A full re-run was required because E4 changed match-generation code (the scheduler).

| New control | Historical parent (`v6-e3-matrix-v1-634132ec3c15`) | F1 | F2 | F2-P | F4 | Mismatches |
|---|---|---|---|---|---|---|
| C-E4 | T-E3 (generated at `6f0fd3f`, `engine/src` `67b73c9a…`) | 2,304 / 2,304 | 576 / 576 | 288 / 288 | 640 / 640 | 0 |
| C-E4K1 | T-E3K1 (same) | 2,304 / 2,304 | 576 / 576 | 288 / 288 | 640 / 640 | 0 |

In all, **7,616 cells are byte-identical to the preserved E3 treatment corpus**. The historical cells were generated before `scheduler_pass_order` existed, and the new controls from the E4 implementation tree. This is P8's forward-path byte identity, confirmed at full matrix scale in both parents. Where a historical field is larger than the E4 field (F1 without `e2_counter`, F2-P in one orientation), the comparison covers exactly the E4 cells.

In the same record, per field and condition:

- **E3 telemetry continuity.** The E3 analyzer on the re-run control reproduces E3 freeze v1's frozen telemetry cell for cell: 7,616 cells, 0 differing, 0 missing.
- **Integrity.** E4's orientation-aware copy of E2's `corpus_integrity` passes. It checks:
  - the exact frozen cell set, with no duplicates or extras;
  - every cell complete;
  - the Ruleset in every result;
  - the frozen digests, freeze id, condition, field and fingerprints in `provenance.json`;
  - a generating commit (`e0d39b3`) whose `engine/src` is the frozen tree.

  E2's frozen check always expects both orientations and would misreport F2-P. A test shows the two agree on F1 and differ only there.
- **Clean telemetry** in every cell.

## Twin relabel gate

**PASS**, in the same record, for both conditions: F2 288 pairs, F4 32 pairs (the jam mirror), 0 failures. For every seed, the two orientations' replay tick records are byte-identical and name the same winning seat (O-RELABEL). Mirror metrics are computed only after this gate passes.

## Analyzer qualification (control data only)

**PASS** (`analyzer_qualification.json`, SHA-256 `4d30af76388d094a8b0f8b9cfd977340282ec422d7a3a5d35feac8b35e661a48`). The E4 telemetry ran over every replay of both new controls and of the E4-field subset of both historical parents. A second, independent pass then recomputed every row.

| Corpus | Replays | Failures | `cpu_used` ≠ `cpu_total` | Capture-engine disagreements | Ownership / E4 reconstruction disagreements | FPS identity failures | Second-pass differences |
|---|---|---|---|---|---|---|---|
| New C-E4 | 3,808 | 0 | 0 | 0 | 0 / 0 | 0 | 0 |
| New C-E4K1 | 3,808 | 0 | 0 | 0 | 0 / 0 | 0 | 0 |
| Historical T-E3 (E4 field) | 3,808 | 0 | 0 | 0 | 0 / 0 | 0 | 0 |
| Historical T-E3K1 (E4 field) | 3,808 | 0 | 0 | 0 | 0 / 0 | 0 | 0 |
| **Total** | **15,232** | **0** | **0** | **0** | **0 / 0** | **0** | **0** |

- **Attribution and checks.** Capture attribution mismatches and E4 check failures are both 0. Exclusive ticks and zero-action live ticks are 0 in every corpus, as λ = 1 requires.
- **`DECIDED_EARLY`.** 4,788 cells are counted as `DECIDED_EARLY` and none is dropped. For example, C-E4 F1 has 519 decided-early, 881 neutral, 776 moderate-last and 128 strong-last cells.
- **Static cells.** 966 cells have a defined FMA with zero swings, all of them mirror cells. PM-1 keeps them `NOT_SCOREABLE`, and FMA scores them. Nothing is converted into neutral.
- **Pinned files.** Each qualified telemetry file's SHA-256 is recorded, and the unlock re-verifies it.

## Frozen control populations

`tools/research/v6/e4/control_populations.json`, SHA-256 **`56a8c1090b27929cb8b33fc861f385dacb8898d86e673ee6a42505e8eeef06c5`**, is committed and pinned in the freeze record.

- **Provenance.** It was computed from the new controls after they passed reproduction. An independent earlier computation produced the same bytes. The unlock recomputes it and requires exact equality, and it is never recomputed from treatment data.
- **Contents per arm:**
  - every unit's control FMA summary, band and contest class;
  - P-PAR and its split by contest class;
  - the mirror seed units;
  - the exposed F1 cells, their non-capture subset and their tick-limit count;
  - the seat metrics and mirror claims;
  - the control-vs-control census and hypothesis readings.
- **P-STALE** is frozen once.

| Arm (control) | Units | DECIDED-EARLY units | P-PAR | P-PAR by class (MULTI-PASS / OPENING-ONLY / INCIDENTAL) | Exposed F1 | Non-capture exposed F1 |
|---|---|---|---|---|---|---|
| Primary (C-E4) | 109 (F1 72, F2 9, F2-P 9, F4 19) | 32 | **32** (F1 29, F2 3) | 18 / 14 / 0 | 2,304 | 1,463 |
| Companion (C-E4K1) | 109 | 38 | 26 (F1 23, F2 3), reported only | 14 / 12 / 0 | 2,304 | 1,209 |

- **Sides.** Every P-PAR unit in both arms is last-side: 4 strong-last and 28 moderate-last in the primary. No unit in either control is first-side.
- **P-STALE** (O-P-STALE) is E3's primary-arm stalemate population restricted to the E4 field: **610 cells**, F1 482 of E3's 610 (the `e2_counter` pairings leave), F2 64 of 64, and F4 64 of 64. It carries no interpretive weight.
- **Evidence labels.** In the primary P-PAR, 21 of 32 units are deterministic characterizations (n_distinct = 1), including 17 of the 18 MULTI-PASS units. 6 are rate-eligible, all OPENING-ONLY. H1 and H2 are therefore census counts over deterministic matchups (§P rule 2), and no rate is claimed from them.

## Control-vs-control census (§P rule 4)

**PASS in both arms, 100% identity classes** (hard stop 11 not triggered).

| Arm | STAYS | UNCHANGED-NEUTRAL | DECIDED-EARLY | FIRST-SIDE-CONTROL | Any other class |
|---|---|---|---|---|---|
| Primary (C-E4 v C-E4) | 35 | 42 | 32 | 0 | **0** |
| Companion (C-E4K1 v C-E4K1) | 29 | 42 | 38 | 0 | **0** |

Every unit with a defined FMA in both arms is STAYS or UNCHANGED-NEUTRAL: 77 of 77 in the primary and 71 of 71 in the companion. The decided-early units are identity by construction, since they are decided early in both copies, and they are counted as their own category. In P-PAR, 32 of 32 units are STAYS.

The hypotheses, read control against itself, are recorded in the populations file:

| E4-H0 | E4-H1 | E4-H2 | E4-H3 | E4-H4 | E4-H5 | E4-H6 | E4-H7 | E4-H8 | D9′ |
|---|---|---|---|---|---|---|---|---|---|
| SUPPORTED | REFUTED | REFUTED | SUPPORTED | REFUTED | REFUTED | REFUTED | NEITHER | REFUTED | HOLDS |

On an identity "treatment", the rows "H0" and "¬H1 ∧ H3" apply. See finding P-1 below.

## Control baseline

These are control facts, not E4 results.

| Quantity | C-E4 (primary) | C-E4K1 (companion) |
|---|---|---|
| Cell FMA bands, F1 | DECIDED_EARLY 519 · neutral 881 · moderate-last 776 · strong-last 128 | 647 · 926 · 603 · 128 |
| Cell FMA bands, F2 (F2-P) | DECIDED_EARLY 68 (34) · neutral 306 (153) · moderate-last 202 (101) | the same |
| Cell FMA bands, F4 | DECIDED_EARLY 480 · neutral 160 | 544 · 96 |
| PM-1, F1 | 1,395 scored, 909 `NOT_SCOREABLE` | 1,137 scored, 1,167 |
| H4 cell set: exposed F1 MULTI-PASS cells | 640 | 640 |
| H5 baseline: non-capture exposed F1 cells | 1,463 | 1,209 |
| H6 baseline: exposed-F1 tick-limit share | 1,463 / 2,304 = 0.635 | 1,209 / 2,304 = 0.525 |
| F1 seat metrics | no unit with SDom ≥ 0.9 or SCD ≥ 0.5; max \|GSB\| 0.016 | one unit with SCD ≥ 0.5 (greedy painter v guarded painter); max \|GSB\| 0.5 |
| F2 mirror claims | guarded painter `seed_conditioned` (19/13, SCD 13/16, n_distinct 32); the other 8 `not_seat_determined`; max \|GSB\| 0.1875 | all 9 `not_seat_determined`; max \|GSB\| 0.094 |
| Mirror claims at 1000 v 1001 | all 9 agree | all 9 agree |
| Completions against repair and disrupt guards and twins (D9′ victims), all fields | 0 (G.5 under the T-E3 Ruleset) | 192 |

## Pre-treatment findings (control data only; nothing changed)

These were found on control data before any treatment exposure. Each is reported, and none was acted on. The pre-registration is not edited.

- **P-1. A no-effect treatment satisfies both "H0" and "¬H1 ∧ H3".** Control against itself, every P-PAR unit is STAYS, so E4-H0 is SUPPORTED. But E4-H3's criterion (STAYS ≥ 2/3 of OPENING-ONLY P-PAR) is also met, and E4-H1 is REFUTED. The "¬H1 ∧ H3" row ("the residual is the opening-pass effect; the in-tick order line closes") therefore applies alongside "H0".
  - H3's STAYS criterion alone cannot tell an opening-pass privilege from no effect at all.
  - Both rows close the in-tick order line, so they do not contradict each other. They differ in what they attribute the residual to, and under O-INTERPRETATION both would be reported.
  - This is a property of the registered criteria, not a tooling defect.
  - The ways forward, both before any treatment exists: accept it as a registered limitation, or re-register under a new analysis freeze v2, still blind to treatment. This phase does neither.
- **P-2. P-PAR sits close to the neutral boundary.** 8 of the 32 primary P-PAR units have a control median within 0.01 of −0.5. Two are exactly −0.5, which O-FMA-BAND places in moderate-last.
  - A small treatment shift can therefore move them to NEUTRALIZED, or keep them as STAYS.
  - The bands are integer-resolution by design (§M.2), and this is recorded, not adjusted.
- **P-3. MULTI-PASS P-PAR is almost entirely deterministic.** 17 of its 18 units have n_distinct = 1, and none is rate-eligible. H1 and H2 read census counts of deterministic characterizations, which is what §P rule 2 prescribes.
- **P-4. The D9′ parity condition is vacuous on the primary Ruleset.** See below. The real guards never reach a zero core under T-E4's Ruleset in any D9′ scenario, so "no zero-core evaluation on the guard's own first-mover ticks" holds trivially there. The condition is exercised by the parity-sensitivity arm, where it fires.

## G.4′ manipulation gate

**PASS** (`manipulation_gate.json`, SHA-256 `2ad547ea4a2ac3186e0d9cc919d1d47e4ffef6410e4262df0914d55d8c9e447b`). It is run per treatment arm against its parent, and every check is a manipulation check, not a treatment finding.

| Check | T-E4 Ruleset | T-E4K1 Ruleset | Each forward parent (sensitivity) |
|---|---|---|---|
| Runtime offer sequence, scripted idle controller, ticks 1–4 | `FFLLFFLLLLFFLLFF` every tick, slots in order | the same | `FFLLFFLLFFLLFFLL`, as it must be |
| Exhaustive jam bound (single-process, co-located, spread layouts; 256 / 256 / 6,561 jam patterns per role) | minimum executed (first, second) = **(5, 5)**, no zero | (5, 5) | (5, 4): the G.4 bound, not G.4′ |
| Fixture checks: jam sniper v each of the 9 agents and its twin, seed 42, 1000 ticks | PASS: second-mover minimum 5, no G.4′ violation, no exclusive or zero-action tick, final-chunk owner the first mover | PASS | FAIL against the mirrored checks: 7 G.4′ violations, 10 final-chunk-owner violations |

## D9′ real-fixture gate

**PASS** (`d9_prime_real_fixture_gate.json`, SHA-256 `532d268bbc12d9fa97bcbc530448b097b1de67da5d8adc4c4f197ac6b8d7a4db`). It reuses E3's D9 scenario machinery unchanged:

- **Guards.** The real, tracked `e2_repair_guard` and `e2_disrupt_guard`, loaded exactly as a match loads them. Their twins' `agent.py` files are byte-identical to theirs.
- **Adversaries.** Eleven scripted ones: omniscient, anchor, alternating, and eight seeded random jammers. None is a matrix entrant.
- **Settings.** Seeds 42, 1001 and 1002, all outside the matrix; both guard seats; 1000 ticks.
- **Analysis.** Each replay is read back by the E4 telemetry.

| | Primary: T-E4 Ruleset | Capture sensitivity: whole-tick K = 2 parent | Parity sensitivity: forward T-E3 Ruleset |
|---|---|---|---|
| Scenarios | 132, all to tick 1000, guard alive | 132 | 132, all to tick 1000 |
| Completions against the guard | **0** | repair guard captured in **60 of 66**; the six not captured are the pure anchor jammer | 0 (G.5) |
| Zero-core evaluations of the guard | **0** (maximum streak 0) | — | **3,360, all on the guard's own first-mover ticks** (the disrupt guard, in 9 scenarios against the omniscient and alternating adversaries) |
| Minimum executed actions (first / second mover) | **5 / 5** | — | 5 / 4 |
| Final-chunk owner | the first mover, in all 132 | the second mover | the second mover |
| Exclusive ticks, zero-action live ticks, analyzer problems | 0, 0, 0 | — | 0, 0, 0 |

Both negative controls fire:

- whole-tick disruption lets the repair guard be captured;
- the forward order lets the disrupt guard evaluate at zero on its own first-mover ticks, which the mirrored parity condition forbids.

On the primary, the parity condition cannot fire, because the guards never reach zero (P-4). This is an implementation-consistency gate. It is not a treatment result, and no matrix cell was exposed.

## Treatment gates (implemented; exercised on control data only)

For the future treatment, `run_e4 treatment-gates` runs:

- integrity;
- the relabel gate;
- the G.4′ manipulation checks on every cell: second-mover and first-mover minimum 5, no exclusive or zero-action live tick, the final-chunk owner the first mover, and the `cpu_used` cross-check;
- for T-E4, the D9′ stop.

There is no prefix gate, because order differs from tick 1 (review §R). When the C-E4 control sample is presented as a treatment, the gates **fail**, on final-chunk-owner violations in F1 and G.4′ violations in F4. That failure is the intended behaviour.

## Clean-checkout reproducibility

A `git archive` of `6815cab` was extracted to a scratch directory. Its root `agents/` runtime catalogue was deleted, so nothing could resolve from it, and every import was forced to resolve from the export (`PYTHONPATH` = export `engine/src` and export root; each module's `__file__` was checked).

| Check | Result |
|---|---|
| `battle_engine`, the harness, capture analyzer v2, E3 action/parity analyzer v1 and every E4 module import from the export; the harness's `REPO_ROOT` is the export | yes |
| No `.git`; no root `agents/` directory | yes; yes |
| All 20 matrix entrants (9 agents, 9 twins, the jam sniper and its twin) resolve from tracked sources, and their live fingerprints equal the frozen ones | 20 / 20 |
| Matrix loads and verifies; id `v6-e4-matrix-v1-fc29d575dd25`; count | yes; 15,232 |
| Real-planner dry run | 15,232 planned, all consistent |
| Contest-class table loads and re-derives; SHA-256 `47097041…` | yes |
| Pre-registration loads; SHA-256 `56307844…`; E4-H0–H8 and D9-PRIME | yes |
| Capture analyzer v2 (version 2) unchanged against E2 freeze `v6-e2-freeze-v2-db6458596d82`; E3 freeze `v6-e3-freeze-v1-506811e78ad8` loads | yes; yes |
| E4 freeze `v6-e4-freeze-v1-101a941f5e30` loads against the exported tooling; control qualification PASS | yes |
| `control_populations.json` loads at its pinned SHA-256 `56a8c109…`; both censuses PASS | yes |

The six E4 test modules also run from the export: 134 passed, 1 skipped and 7 failed.

- **The skip** is the check against the git-ignored preserved E3 corpus, which an export does not have.
- **The seven failures** are the freeze-identity tests that derive the live identity from `git rev-parse`. They fail with `fatal: not a git repository` and pass in the checkout.
- **What still runs.** The freeze itself loads from the export, as the table shows, and the committed control-qualification test passes there.

## Mutation testing

Each mutation was applied to the committed tooling (`6815cab`), and its detecting tests were run. The file was then restored byte for byte from `HEAD`, and the tree was verified clean before the next mutation. Nothing was committed.

| # | Mutation | File | Detected by (failing tests) |
|---|---|---|---|
| M1 | FMA sign flipped | `cell_metrics.py` | `test_fma_is_half_the_parity_difference_of_the_mean_balance`, `test_forward_sweep_is_a_strong_last_mover_lock` (2) |
| M2 | FMA ½ multiplier dropped | `cell_metrics.py` | `test_fma_is_half_the_parity_difference_of_the_mean_balance`, `test_forward_sweep_is_a_strong_last_mover_lock` (2) |
| M3 | FMA parity assignment swapped | `cell_metrics.py` | `test_forward_sweep_is_a_strong_last_mover_lock` (1) |
| M4 | Static zero-swing cells made `NOT_SCOREABLE` (FMA gated on ≥ 10 swings) | `cell_metrics.py` | `test_mirrored_sweep_is_static_and_its_fma_is_defined_without_swings` (1) |
| M5 | FMA band boundary drifted (0.5 → 0.6) | `cell_metrics.py` | `test_fma_band_boundaries_follow_the_registered_inequalities` (1) |
| M6 | FPS uses the first mover instead of the final-chunk owner | `cell_metrics.py` | `test_a_reconstruction_disagreement_is_reported`, `test_forward_sweep_is_a_strong_last_mover_lock` (5) |
| M7 | FOLLOWS-FINAL misclassified (as NEW) | `analyze_e4.py` | `test_h2_follows_the_final_chunk`, `test_neither_satisfies_neither_side_so_no_row_applies`, `test_transition_classes_partition_in_the_registered_precedence` (4) |
| M8 | Twin-mirror orientations counted as two units | `analyze_e4.py` | `test_d9_prime_is_a_stop_not_a_result`, `test_h0_no_structural_effect_and_the_none_row`, `test_h1_h3_not_h2_is_the_two_mechanism_row`, … (11) |
| M9 | SDom and SCD formulas swapped | `analyze_e4.py` | `test_pairing_seat_metrics_follow_sec_m1` (1) |
| M10 | `e2_counter` reintroduced into F1 | `matrix.py` | `test_contest_class_table_is_frozen_and_derives_from_the_source_roles`, `test_dry_run_counts_one_field_with_the_real_planner_and_runs_nothing`, `test_fields_and_expected_match_counts`, … (8) |
| M11 | A contest class edited after the fact, as if from outcomes (sniper v disrupt guard → OPENING-ONLY) | `contest_classes.json` | `test_contest_class_table_is_frozen_and_derives_from_the_source_roles`, `test_contest_classes_match_every_pairing_the_review_classifies`, `test_matrix_definition_is_frozen`, … (5) |
| M12 | n_distinct ignored (cells counted instead) | `analyze_e4.py` | `test_duplicated_seed_trajectories_are_one_distinct_transition` (1) |
| M13 | Control-vs-control emits a non-identity class (same band → STRENGTHENED) | `analyze_e4.py` | `test_a_control_against_itself_is_always_an_identity_class`, `test_h0_no_structural_effect_and_the_none_row`, `test_h1_h3_not_h2_is_the_two_mechanism_row`, … (7) |
| M14 | 1000/1001 mirror disagreement ignored | `analyze_e4.py` | `test_a_1000_1001_claim_disagreement_is_flagged` (1) |
| M15 | F4 pooled into the standard population | `analyze_e4.py` | `test_p_par_takes_non_neutral_standard_units_only` (1) |
| M16 | A request override allowed | `run_e4.py` | `test_any_request_override_fails_closed` (4) |
| M17 | Parent reproduction mismatch ignored | `gates.py` | `test_parent_comparison_accepts_a_byte_identical_copy_and_catches_tampering` (1) |
| M18 | D9′ violation ignored | `analyze_e4.py` | `test_d9_prime_is_a_stop_not_a_result` (1) |
| M19 | Scheduler manipulation sequence mismatch ignored | `manipulation_gate.py` | `test_a_sequence_mismatch_fails_the_gate` (1) |
| M20 | Matrix count drift (F2-P given both orientations) | `matrix.py` | `test_dry_run_counts_one_field_with_the_real_planner_and_runs_nothing`, `test_fields_and_expected_match_counts`, `test_frozen_setting_drift_fails_closed`, … (7) |
| X1 | *(extra)* Relabel gate ignores tick-record differences | `gates.py` | `test_the_relabel_gate_passes_twin_mirrors_and_fails_a_changed_tick` (1) |
| X2 | *(extra)* D9′ scenario ignores zero-core evaluations on the guard's own first-mover ticks | `d9_gate.py` | `test_a_violation_fails_the_scenario` (1) |

All 22 were detected: the twenty required breaks and two extras. After every restore the file equalled `HEAD` byte for byte, the tree was clean, and `HEAD` was unchanged (`6815cab`).

## Tests

| Module | Tests | Covers |
|---|---|---|
| `test_v6_e4_matrix.py` | 53 | Counts (15,232); the frozen digest; one-field Ruleset differences; the 9-agent roster without `e2_counter`; contest-class derivation and tamper; fingerprint drift; override and setting guards; the treatment's separate authorization; the treatment-artifact STOP; E4-H0–H8, D9′, metrics, interpretation, evidence rules and hard stops verbatim against the preserved review |
| `test_v6_e4_cell_metrics.py` | 11 | Exact FMA, bands, FPS and final-chunk ownership on real forward and mirrored replays (review §L-1); `DECIDED_EARLY`; static zero-swing cells; reconstruction tamper cases |
| `test_v6_e4_analysis.py` | 42 | Every transition class and the O-TRANSITION order; unit medians; the census and n_distinct; P-PAR; seat and mirror metrics; mirror claims and the 1000/1001 rule; every hypothesis branch; the interpretation rules; the D9′ stop |
| `test_v6_e4_pipeline.py` | 9 | A real two-seed C-E4 sample of every field through telemetry, parent reproduction, E3 continuity, the relabel gate, both integrity checks, the populations and census, and the treatment gates, each with tamper cases; the sample reproduces the preserved T-E3 cells |
| `test_v6_e4_gates.py` | 17 | The reduced D9′ gate on the real guards and its sensitivity; scenario violations; only the full registered gate unlocks; the runtime offer sequences; the full G.4′ gate; a sequence mismatch fails it |
| `test_v6_e4_freeze.py` | 10 | The separate freeze identity; drift detection; reused-file and capture-analyzer pinning; the unlock chain; the committed freeze; the committed control qualification and populations |

## Treatment readiness

`python -m tools.research.v6.e4.run_e4 unlock` reports `{"unlocked": true}` at `6815cab`. The command is read-only and executes nothing. Before any treatment can run or be analyzed, the unlock chain requires all of the following:

1. The committed freeze `v6-e4-freeze-v1-101a941f5e30` still holds against the live tooling; capture analyzer v2 and every reused E3 file are byte-identical to their pins.
2. Its `control_qualification` is `PASS`, and the parent-reproduction, analyzer-qualification, manipulation and D9′ records match their pinned SHA-256.
3. Those records are complete, non-sample, passing and under this freeze, and the relabel gate passes in every F2 and F4 field.
4. The qualified control telemetry files are unchanged.
5. `control_populations.json` matches its pinned SHA-256, recomputes exactly from the control corpus, and its census is 100% identity classes.

Execution then additionally requires `--confirm-matrix-execution --confirm-treatment-execution`, a clean tree, and the frozen engine and tooling source, checked before and after the run.

**Order for the separately authorized treatment phase:**

1. `execute T-E4 <field>` for F1, F2, F2-P and F4, then the same for T-E4K1.
2. `treatment-telemetry` for each treatment.
3. `treatment-gates` for each treatment. Any failure is a STOP. A D9′ completion under T-E4 is a theorem violation, which is an implementation STOP. So is a relabel failure, a G.4′ violation or a final-chunk-owner violation.
4. `analyze`, which writes the criterion statuses for the primary arm and the companion's H4 reading. Verdicts are then read under the interpretation table.

Before authorizing the treatment, decide P-1 (H0 and "¬H1 ∧ H3" co-apply under no effect).

## Treatment-Ruleset exposure in this phase

**No matrix cell ran under a treatment Ruleset, and no treatment corpus exists.** No `T-E4` or `T-E4K1` directory exists under the run root, and the runner's treatment-artifact check finds none.

This phase's own work ran the following under the treatment Rulesets, all at non-matrix seeds or with non-matrix entrants:

- **G.4′ manipulation gate** (both treatment Rulesets):
  - a scripted idle controller, 4 ticks;
  - the exhaustive jam bound, which runs the policy's own scheduler, not a match;
  - the jam sniper against each of the 9 agents and its twin at seed 42, 1000 ticks, jam sniper in Seat A. These are the F4 pairings in one orientation at a seed outside 1–32.

  It ran once for the gate record, again in the test suite, and in development trials. Only the manipulation checks were read.
- **D9′ gate** (T-E4 Ruleset): the real guards against scripted adversaries at seeds 42, 1001 and 1002. Its reduced form is in the test suite (seed 42, two adversaries).
- **One cell-metrics test:** sniper v disrupt guard at seed 42, 1000 ticks (the review's §L-1 trace, whose mirrored behaviour the review itself reports).

**Pre-existing exposure (implementation phase, `4d4ede7`).** The committed Ruleset tests, `test_ruleset_v6_research_mirrored_passes.py`, run the following under both treatment Rulesets and their parents:

- sniper v disrupt guard, spread sniper v disrupt guard, and the probe mirror, at **seed 7** for **60 ticks**, to assert determinism, distinct result identities and an unchanged replay shape;
- scripted non-matrix scenarios at seed 1.

Seed 7 is a matrix seed, and no fixture reads the tick limit. Each of those runs therefore equals the first 60 ticks of the corresponding matrix cell (F1, and the F2 / F2-P candidate-first cell). They assert mechanics only. They ran unchanged in this phase's repository suites, and nothing from them was analyzed or used here.

The design review's §L probe traces (seed 42) had already reported the named scenarios' mirrored behaviour.

## What this record does not claim

- No E4 gameplay result, and no hypothesis verdict. Neither T-E4 nor T-E4K1 was run. The control-vs-control readings above are identity checks, not E4 findings.
- No prediction that mirrored passes improve gameplay. The probe priors are predictions to be falsified.
- No threshold, operationalization, population or contest class tuned or changed after the E4 controls ran:
  - the pre-registration and contest classes were committed at `6184f12` and frozen at `e0d39b3`, before any E4 control cell existed;
  - during development, preserved E3 corpus cells were read to validate the analyzer and to de-risk the 9-agent field and one-orientation F2-P;
  - findings P-1 to P-4 were found after the controls ran, and they were reported rather than acted on.
- No change to gameplay, the qualified E4 Rulesets, the scheduler, the replay or result schema, capture analyzer v2, E3 action/parity analyzer v1, E2, E3 or V4.
