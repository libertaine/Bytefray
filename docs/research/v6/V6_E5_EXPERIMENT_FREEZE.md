# Bytefray V6 E5 — Anchor/Core-0 Separation: Research Tooling, Pre-registration and Experiment Freeze

**Status:** The E5 research tooling is built and qualified. The experiment is frozen, and both controls (C-E5, C-E5K1) have been run and qualified. **Neither treatment condition (T-E5, T-E5K1) has been run.** Nothing in this record is a gameplay result, and no E5 conclusion is drawn.
**Branch:** `v6-research`. Reviews preserved at `4fbd1d4`; E5 parent byte-identity freeze at `8f6717d`; Rulesets implemented at `e0a1b02`; tooling committed at `76c1d625c83c39cf353e28db37ca2d756bd53d55`; analysis freeze committed at `aab8fa4d7a3f809b3476ac20dae20d2095ab7fe9`; controls generated at `a6d11167b1ae957ff382b35a7ebef947c234ebb8`; control qualification committed at `4d889e05e0473429f07c48bea952e9dbc406a816`; mutation-gap tests at `acba511`.
**Authority:**
- [`V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md`](V6_E5_ANCHOR_CORE_SEPARATION_DESIGN_REVIEW.md) (verdict REDESIGN), preserved verbatim at `4fbd1d4` (SHA-256 `63d79246c4cf3e3787c10e3862cbc8fb8fefbe51517f65aa23dea066a46ac17d`).
- [`V6_E5_DESIGN_REVIEW_REVISION_1.md`](V6_E5_DESIGN_REVIEW_REVISION_1.md), preserved verbatim at `4fbd1d4` (SHA-256 `35b9022f242207c5bd8514b5c066c1c1a86a1e8dfca7dfc0f63a438dd2451998`).
- The research lead's decisions R1-1 to R1-5 and O-1 to O-5, recorded in [`V6_E5_ANCHOR_CORE_SEPARATION_REGISTRATION.md`](V6_E5_ANCHOR_CORE_SEPARATION_REGISTRATION.md) (`fa9abef`) and carried verbatim in the pre-registration.

## Scope

This phase carries out the authorized sequence up to its stopping point:

1. review commits;
2. the E5-parent byte-identity freeze;
3. the Ruleset implementation and its tests;
4. the E5 tooling and analyzers;
5. the pre-registration and the matrix and analysis freezes;
6. control execution, parent reproduction and analyzer qualification;
7. the frozen control populations;
8. the non-matrix manipulation gates.

It stops there, blind. **No T-E5 or T-E5K1 matrix directory, cell or telemetry exists**, and no treatment BP value has been recorded or read (see "Treatment-Ruleset exposure" for every place separation ran).

No gameplay code changed after the Ruleset implementation. `engine/src` is byte-identical to the implementation tree (`da3f9ac2b5268cbe5bbcfa4701ea076554598d35`, commit `e0a1b02`) at every later commit of this phase. The core, its seeding and recorded `pc`, the scheduler, capture, K, λ, scoring, rotation, quota, process selection, movement and the replay and result schemas are untouched. Capture analyzer v2, E3 action/parity analyzer v1, the E4 cell metrics and every other reused E2, E3 and E4 module are reused byte for byte, by import, and are pinned.

## Where things live

| Path | Contents |
|---|---|
| `tools/research/v6/e5/cell_metrics.py` | Per-cell O-BP and the E5-D quantities (version 1), with cross-checks against the reused analyzers |
| `tools/research/v6/e5/telemetry.py` | Per-cell telemetry for a whole corpus: E4's telemetry (E3 action/parity, capture analyzer v2, E4 FMA/FPS) plus the E5 cell metrics; JSONL, repeatability digests |
| `tools/research/v6/e5/analyze_e5.py` | E5 analyzer v1: directed units, unit BP, bands, transition classes, contest classes, the census, statuses, E5-H1–H5, pathology flags, D9 and the fail-closed interpretation |
| `tools/research/v6/e5/matrix.py` | The frozen experiment definition and its digest |
| `tools/research/v6/e5/preregistration.json` / `preregistration.py` | E5-D, E5-H1–H5, PATHOLOGY, D9, the operationalizations, decisions, interpretation table, evidence rules and hard stops; digest pinned; the table's totality is checked on load |
| `tools/research/v6/e5/gates.py` | Parent reproduction (E4's comparison plus the E5 metrics), E5-D treatment side (D-1–D-5), manipulation checks, D9 |
| `tools/research/v6/e5/nonmatrix_gates.py` | The test-only offset-aware fixture copies, the P5 inertness gate, the observation-delta gate and the D9 real-fixture gate |
| `tools/research/v6/e5/populations.py` / `control_populations.json` | The frozen control populations, the control-side E5-D clauses, O-MIN-SB and the control-vs-control evaluation |
| `tools/research/v6/e5/analysis_freeze.py` / `analysis_freeze.json` | The analysis freeze identity and its committed record |
| `tools/research/v6/e5/run_e5.py` | The runner: `plan`, `execute`, `telemetry`, `reproduce`, `qualify`, `populations`, `p5`, `observation`, `d9`, `unlock`, and, for after authorization only, `treatment-telemetry`, `treatment-gates` and `analyze` |

No new fixture was added. E5 reuses seven E2 fixtures and their twins from tracked sources. The offset-aware copies exist only inside the non-matrix gates' temporary data roots; they never enter the matrix, the populations or the analysis.

## The instrument

### Cell metrics (`cell_metrics.cell_metrics`)

Each cell's metrics are read from one canonical replay. The cores are the tick-0 seeding runs at each recorded `pc`, and **the base is core cell 0 at `pc`, never the anchor**. On every replay the metrics must agree with E4's both-alive tick counts and with capture analyzer v2's final owned cells. Any difference is counted as a reconstruction disagreement.

| Quantity | Definition |
|---|---|
| **O-BP** | For victim V: BP_V = (share of V's second-mover ticks at whose end V owns its base) − (share of V's first-mover ticks at whose end V owns it), an exact rational in [−1, 1], over both-alive ticks. The value is DEFINED only with at least 10 both-alive ticks of each parity; otherwise it is `DECIDED_EARLY`, which is counted and never dropped. |
| **D-1** spawn mode | The tick-0 anchor offsets from `pc`: `core_base` (all 0), `before_core` (all −1) or `other` |
| **D-2** default dual writes | Hostile writes to a still-unmoved spawn anchor that are also writes to the victim's core |
| **D-3** DUAL | Hostile writes that hit a victim process's anchor (at the t−1 or t boundary) and a cell of that victim's core, whether or not the process moved |
| **D-4** own-core occupancy | Process-boundaries at which a process sits on its own core |
| Directed counts | Per attacker→victim: unmoved-anchor hits, ambiguous anchor hits, core-0 writes, default-anchor core-0 writes, dual writes, mean core coverage and first contact tick |

### Analysis (`analyze_e5`)

- **Directed units (O-BP-UNIT).** Each round-robin ordered matchup gives two directed units, one per victim seat. A twin mirror is one unit observed on its candidate-first cells. Its per-seed value is the mean of its two victims' BP (O-1), and both directed values are kept descriptively.
- **Unit BP.** The exact median of the per-seed cell values. Raw ticks are never pooled across seeds. A unit is DECIDED-EARLY with no DEFINED cell or with fewer than half.
- **Bands (O-BP-BAND).** Exact edges, closed away from neutral:

  | Band | Range |
  |---|---|
  | second-strong | BP ≥ 2/3 |
  | second-moderate | 1/3 ≤ BP < 2/3 |
  | neutral | \|BP\| < 1/3 |
  | first-moderate | −2/3 < BP ≤ −1/3 |
  | first-strong | BP ≤ −2/3 |

  A unit within 1/50 of an edge is flagged `near_boundary`.
- **Transition classes (O-TRANSITION-E5).** Nine classes, tested in this order, which partitions every (control, treatment) pair:
  1. DECIDED-EARLY;
  2. FIRST-SIDE-CONTROL;
  3. UNCHANGED-NEUTRAL;
  4. NEW;
  5. NEUTRALIZED;
  6. FLIPPED;
  7. STAYS;
  8. WEAKENED;
  9. STRENGTHENED.

  The E5-H1 numerator is NEUTRALIZED + WEAKENED + FLIPPED (O-2). The E5-H2 numerator is STAYS + STRENGTHENED. The two are disjoint.
- **Contest classes (O-CONTEST-E5).** Each directed unit is classed from the attacker's E4 sweep role and capture analyzer v2's core-inference audit in every control cell, never from BP:
  - **SWEEP-BACKED**: the attacker sweeps, and it inferred the victim's core correctly in every control cell;
  - **ANCHOR-ONLY**: the attacker does not sweep, or it never inferred the core;
  - **MIXED-INFERENCE**: anything else. These units are frozen, reported and excluded from E5-H1 and E5-H2 (O-5).
- **P-BASE (O-P-BASE).** The directed units whose control unit BP is DEFINED and second-side (BP ≥ 1/3; O-3).
- **Statuses (O-STATUS-E5).** SUPPORTED iff the value is ≥ `supported_min`. REFUTED iff it is ≤ `refuted_max`. Otherwise NEITHER, and NOT_EVALUABLE with no units. **NEITHER never stands for REFUTED.**
- **Interpretation (O-INTERPRETATION-E5).** An explicit table over (E5-D, E5-H1, E5-H2):

  | Row | Status combinations |
  |---|---|
  | STOP | E5-D FAIL, with all 8 possible combinations |
  | R-H2 | (REFUTED, SUPPORTED) |
  | R-H2-PRIME | (NEITHER, SUPPORTED) |
  | R-H1 | (SUPPORTED, REFUTED) |
  | R-H1-PRIME | (SUPPORTED, NEITHER) |
  | NONE | the four NEITHER/REFUTED mixes |

  The **impossible** combinations are (SUPPORTED, SUPPORTED) and any NOT_EVALUABLE. The table is total over all 32 inputs. The loader rejects a gap or an overlap. `interpret` raises `InterpretationInvariantError` on an impossible combination, and on any input matched by no row or by more than one. So simultaneous SUPPORTED is an invariant violation, never resolved by precedence.

## Frozen experiment definition

Matrix **`v6-e5-matrix-v1-ef7fa327ea81`** (digest `ef7fa327ea81904c3f8e21161b3c5472837822e298a960d1b3087be8d2388d28`), 7,168 matches.

| Condition | Role | Ruleset | K | λ | Pass order | Spawn | Reproduces |
|---|---|---|---|---|---|---|---|
| C-E5 | control | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1` | 2 | 1 | forward | `core_base` | C-E4 |
| T-E5 | treatment | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1-anchor-before-core` | 2 | 1 | forward | `before_core` | — |
| C-E5K1 | control | `bytefray-rules-6-research-disruption-slot1` | 1 | 1 | forward | `core_base` | C-E4K1 |
| T-E5K1 | treatment | `bytefray-rules-6-research-disruption-slot1-anchor-before-core` | 1 | 1 | forward | `before_core` | — |

- **Fields.**
  - **F1:** the triangular round robin of the seven E5 fixtures, 21 pairs × 32 seeds × 2 orientations = 1,344 per condition.
  - **F2:** the seven twin mirrors × 32 seeds × 2 orientations = 448 per condition. The duplicate orientation is used only by the relabel gate.
- **Common settings.** Seeds 1–32, 1,000 ticks, arena 512, quota 8.
- **Agents.** The seven E5 fixtures are `e2_sniper`, `e2_repair_guard`, `e2_disrupt_guard`, `e2_min_guard`, `e2_guarded_painter`, `e2_spread_sniper` and `e2_spread_defender`. All 14 fingerprints (fixtures and twins) are pinned.
- **Excluded by decision R1-2, with reasons frozen:**
  - `v4_probe` (anchor-relative target set: the −1 offset is not inert);
  - `e3_jam_sniper` (co-location-authored coverage);
  - `e2_greedy_painter` (writes no enemy anchor);
  - `e2_counter` (writes no enemy anchor under λ = 1).
- **Sweep roles.** Copied from E4's source roles: the sniper, min guard, spread sniper and spread defender sweep; the repair guard, disrupt guard and guarded painter do not.
- **Guards.**
  - Forbidden request overrides: `scheduler_chunk_size`, `scheduler_rotate_start`, `kill_weight`, `instr_per_tick`.
  - Each treatment must differ from its control only in `initial_anchor_placement`, apart from its identity. `verify_ruleset_registry` checks this on every load.

## Hypothesis pre-registration

`tools/research/v6/e5/preregistration.json`, SHA-256 **`6e226fa8e620ff9c62bdbff46c7bc67af2331ae300607a4dcd1f8019a40818f4`**.

| Id | Statement (abridged; verbatim in the file) | Criterion |
|---|---|---|
| E5-D | Decoupling manipulation gate: D-1 spawn = `pc − 1` and D-2 = 0 (Ruleset invariants); D-3 DUAL = 0 and D-4 own-core occupancy = 0 (E5-corpus characterizations); D-5 anchor-induced core-0 contact present in control and absent in treatment for every ANCHOR-ONLY P-BASE unit; D-6 sensitivity | A hard stop; reads no gameplay outcome |
| E5-H1 | Co-location carries the directed base privilege | Share of SWEEP-BACKED P-BASE units in NEUTRALIZED + WEAKENED + FLIPPED: SUPPORTED ≥ 2/3, REFUTED ≤ 1/10 |
| E5-H2 | Co-location is not necessary for the directed base privilege | Share in STAYS + STRENGTHENED: SUPPORTED ≥ 2/3, REFUTED ≤ 1/10 |
| E5-H3 | E4 residual population unchanged in FMA band (continuity only) | (E4 STAYS + UNCHANGED-NEUTRAL) / \|P-PAR-E5\| ≥ 9/10 |
| E5-H4 | Separation changes match outcomes (K = 2) | Outcome-change share of F1 cells: SUPPORTED ≥ 1/10, REFUTED ≤ 1/50 |
| E5-H5 | The hold changes how much separation changes outcomes | \|companion − primary change share\|: SUPPORTED ≥ 1/10, REFUTED ≤ 1/50 |
| PATHOLOGY | PF-1 to PF-5, recorded whatever else holds | Flag at ≥ 1/10 (PF-5: seat SDom ≥ 9/10 or \|GSB\| > 1/10 newly) |
| D9 | G.5 immunity under T-E5 | 0 capture completions against the repair and disrupt guards; a hard stop |

- **Denominator.** DECIDED-EARLY units stay in the E5-H1 and E5-H2 denominator.
- **O-MIN-SB (O-4, as modified).** At least 6 SWEEP-BACKED P-BASE units must exist in the primary arm. With fewer, the experiment halts before treatment and the design is reassessed.
- **Companion arm.** It never replaces a primary verdict.
- **The null signature.** A no-effect treatment reads H1 REFUTED and H2 SUPPORTED. Only E5-D keeps that from reading R-H2 (review AF-11), so control against itself is evaluated with E5-D FAIL and must read STOP.
- **Hard stops.** The file lists 13, including any golden, reproduction, fingerprint, one-field, E5-D, D9, analyzer, relabel, manifest, control-census, O-MIN-SB or non-matrix-gate failure.

## Freeze identities

The two identities are kept apart.

| Identity | Value | Covers |
|---|---|---|
| Matrix | **`v6-e5-matrix-v1-ef7fa327ea81`** | the conditions and their Rulesets; the fields, pairs, seeds, orientations and tick limit; the arena and quota; the roster, the exclusions and the sweep roles; all 14 fingerprints; the forbidden overrides; the historical parents; the counts |
| Analysis freeze | **`v6-e5-freeze-v1-5ba12be258c8`** (digest `5ba12be258c80bd0876542b035bc66d183a9447d4c6c014528aff9f2ea516227`) | the matrix id and digest; the pre-registration SHA-256; E5 analyzer v1 (`analyze_e5.py` `6bc65a26…768538`) and cell metrics v1 (`25c5e0d8…7f964`); the SHA-256 of all 35 tooling files, with every reused E2, E3 and E4 file checked against E4 analysis freeze v1's pins; the tooling commit `76c1d625…`; the match-generation tree `engine/src` = `da3f9ac2…`; the E5 parent freeze (`8f6717d`, 96 matches); and the historical E4 control provenance (E4 freeze `v6-e4-freeze-v1-101a941f5e30`, generated at `e0d39b3`, engine tree `940a27bc…`) |

The freeze record's `control_qualification` block lies outside the identity digest. It was added after the controls passed, and it pins the SHA-256 of the five control-phase records and of `control_populations.json`. The freeze pins no test file, so tests added after it leave the identity unchanged.

## Control execution

Both controls ran through `run_e5 execute CONDITION FIELD --confirm-matrix-execution --workers 1`. They started from `a6d1116` with a clean tree: all four fields in parallel processes, one match worker each.

- **Source checks.** Each field passed the execution-source check before and after its run. A source manifest was taken during the runs, covering `HEAD`, the `engine/src` and `tools/research/v6` trees, and the SHA-256 of 124 files under `tools/research/v6`. It was identical after the runs, and the tree was clean.
- **Failures.** No cell failed, and the Windows `evaluation.json` `PermissionError` seen in E4 did not recur.

| Condition | F1 | F2 | Total | Wall clock (UTC, 2026-09-25) |
|---|---|---|---|---|
| C-E5 | 1,344 | 448 | 1,792 | 01:31:32–01:46:09 |
| C-E5K1 | 1,344 | 448 | 1,792 | 01:31:37–01:45:10 |

The artifacts are under `runs/research_v6_e5/v6-e5-matrix-v1-ef7fa327ea81/{C-E5,C-E5K1}/{F1,F2}`, and every `result.json` and replay is preserved (git-ignored). Each field's `provenance.json` names `a6d1116`, `git_dirty: false` and freeze `v6-e5-freeze-v1-5ba12be258c8`. **No T-E5 or T-E5K1 directory exists.**

## Parent reproduction gate

**FULL PASS** (`parent_reproduction.json`, SHA-256 `ee68117e204892baf7e7278fe140245f9823f81e2c3fd00fd241d1522b920dca`).

Each new control and its preserved E4 control run under the same Ruleset id, so nothing is excused. The comparison covers:
- every harness cell field, including `match_id` and `result_id`;
- the whole `result.json` apart from `completed_at` and `occurrence_id`;
- the replay bytes, by SHA-256;
- the E3 telemetry;
- the E4 FMA/FPS metrics and the E5 BP and decoupling metrics, computed on both copies.

| New control | Historical parent (`v6-e4-matrix-v1-fc29d575dd25`) | F1 | F2 | Mismatches |
|---|---|---|---|---|
| C-E5 | C-E4 (generated at `e0d39b3`, `engine/src` `940a27bc…`) | 1,344 / 1,344 | 448 / 448 | 0 |
| C-E5K1 | C-E4K1 (same) | 1,344 / 1,344 | 448 / 448 | 0 |

In all, **3,584 cells are byte-identical to the preserved E4 control corpus**. The historical cells were generated before `initial_anchor_placement` existed, and the new ones from the E5 implementation tree. This is the `core_base` path's byte identity at full matrix scale in both parents. The historical fields are larger than E5's: E4's F1 is 36 pairs over nine agents, including `v4_probe` and `e2_greedy_painter`, which E5 excludes, and its F2 has nine mirrors. So the comparison covers exactly the E5 cells.

The same record also shows, for each field and condition:
- **Integrity PASS.** The frozen cell set is complete, the Ruleset appears in every result, and `provenance.json` carries the frozen digests, freeze id and fingerprints. The generating commit `a6d1116` has the frozen `engine/src` tree.
- **Clean telemetry** in every cell.
- **Twin relabel gate PASS** for both conditions: F2, 224 pairs, 0 failures.

## Analyzer qualification (control data only)

**PASS** (`analyzer_qualification.json`, SHA-256 `dfefe5f3507a399d05e2e1feb03c4edad864484a5463d39074ebe4fc4f2ff1d8`). The E5 telemetry ran over every replay of both new controls and over the E5-field subset of both historical parents. A second, independent pass then recomputed every row.

| Corpus | Replays | Failures | Reconstruction / capture / CPU / E4 / E5 disagreements | `DECIDED_EARLY` cells | Second-pass differences |
|---|---|---|---|---|---|
| New C-E5 | 1,792 | 0 | 0 | 64 | 0 |
| New C-E5K1 | 1,792 | 0 | 0 | 128 | 0 |
| Historical C-E4 (E5 field) | 1,792 | 0 | 0 | 64 | 0 |
| Historical C-E4K1 (E5 field) | 1,792 | 0 | 0 | 128 | 0 |
| **Total** | **7,168** | **0** | **0** | **384** | **0** |

Every `DECIDED_EARLY` cell is counted, and none is dropped. Each qualified telemetry file's SHA-256 is recorded, and the unlock re-verifies it.

## Frozen control populations

`tools/research/v6/e5/control_populations.json`, SHA-256 **`1cf96a2e48b4c4bcc95d011b2289963a24fed92a555d5ad927de636b718e1737`**, is committed and pinned in the freeze record.
- **How it was computed.** From the new controls, after they passed reproduction.
- **Independent check.** A dry run computed before the freeze from the preserved E4 control corpus produced identical `arms`, `p_par_e5`, `min_sweep_backed` and `control_vs_control_hypotheses` blocks. Only its placeholder `freeze_id` and `preregistration_sha256` differed.
- **Re-verification.** The unlock recomputes the populations and requires exact equality. They are never recomputed from treatment data.

| Arm | Directed units | DECIDED-EARLY | P-BASE | SWEEP-BACKED | ANCHOR-ONLY | MIXED-INFERENCE |
|---|---|---|---|---|---|---|
| Primary (C-E5) | 91 | 4 | **34** | **17** | **15** | **2** |
| Companion (C-E5K1) | 91 | 8 | 32 | 15 | 15 | 2 |

**The primary arm's 17 SWEEP-BACKED P-BASE units** (seat A | seat B | victim) are listed below. The last two columns are the control unit BP and E4's a-priori class, which is a descriptive secondary stratum only.

| Unit | Control BP | E4 class |
|---|---|---|
| F1 disrupt_guard \| min_guard \| A | 1 | MULTI-PASS |
| F1 disrupt_guard \| sniper \| A | 1 | MULTI-PASS |
| F1 guarded_painter \| min_guard \| A | 1 | OPENING-ONLY |
| F1 guarded_painter \| sniper \| A | 1 | OPENING-ONLY |
| F1 min_guard \| disrupt_guard \| B | 1 | MULTI-PASS |
| F1 min_guard \| guarded_painter \| B | 1 | OPENING-ONLY |
| F1 min_guard \| repair_guard \| B | 1/2 | MULTI-PASS |
| F1 min_guard \| sniper \| A | 1 | OPENING-ONLY |
| F1 min_guard \| spread_defender \| B | 1 | OPENING-ONLY |
| F1 sniper \| disrupt_guard \| B | 1 | MULTI-PASS |
| F1 sniper \| guarded_painter \| B | 1 | OPENING-ONLY |
| F1 sniper \| min_guard \| B | 1 | OPENING-ONLY |
| F1 sniper \| repair_guard \| B | 1/2 | MULTI-PASS |
| F1 sniper \| spread_defender \| B | 1 | OPENING-ONLY |
| F1 spread_defender \| repair_guard \| B | 249/500 | MULTI-PASS |
| F1 spread_sniper \| repair_guard \| B | 1/2 | MULTI-PASS |
| F2 min_guard \| min_guard_twin (mirror) | 1 | OPENING-ONLY |

- **Composition.**
  - Bands: 13 second-strong and 4 second-moderate.
  - E4 classes: 9 OPENING-ONLY and 8 MULTI-PASS.
  - No P-BASE unit in either arm is within 1/50 of a band edge.
- **MIXED-INFERENCE (frozen, reported, excluded).** `F1 spread_defender | min_guard | A` and `F1 spread_defender | sniper | A`, both at BP 499/500, in both arms.
- **ANCHOR-ONLY (15), the population D-5 checks.** In every ANCHOR-ONLY unit the attacker is the disrupt guard or the guarded painter, and neither sweeps. The victims are the disrupt guard, guarded painter, min guard, repair guard and spread defender, together with the disrupt-guard and guarded-painter mirrors. The full list is in the record.
- **Companion.** It has 15 SWEEP-BACKED units. `F1 sniper | repair_guard | B` and `F1 spread_sniper | repair_guard | B` are DECIDED-EARLY under K = 1, not reclassified.
- **O-MIN-SB: PASS.** 17 ≥ 6.
- **P-PAR-E5.** 28 of E4's 32 frozen primary P-PAR units have both agents in the E5 field. They are pinned by E4's populations SHA-256 `56a8c109…06c5`.

### Control-side E5-D and the control census

| Check | Primary | Companion |
|---|---|---|
| Control-vs-control census (100% identity classes) | PASS: 34 STAYS, 53 UNCHANGED-NEUTRAL, 4 DECIDED-EARLY | PASS: 32 STAYS, 51 UNCHANGED-NEUTRAL, 8 DECIDED-EARLY |
| D-5 control side: anchor-induced core-0 contact in every DEFINED cell of every ANCHOR-ONLY P-BASE unit | PASS (0 failures) | PASS (0 failures) |
| D-6: DUAL > 0 wherever an unmoved anchor is hit | PASS (0 failures) | PASS (0 failures) |
| Every audited control inference correct | PASS (0 incorrect) | PASS (0 incorrect) |

### Control against itself (evidence rules; review AF-11: the global null must read STOP)

Every hypothesis was evaluated on control data against itself, with E5-D FAIL because the spawn is on the core by construction. The statuses were:

| Hypothesis | Status |
|---|---|
| E5-H1 | REFUTED |
| E5-H2 | SUPPORTED |
| E5-H3 | SUPPORTED |
| E5-H4 | REFUTED |
| E5-H5 | REFUTED |

The interpretation is **STOP**. No pathology flag is raised, and there are 0 D9 completions. This is the global-null signature. It confirms that a no-effect treatment can be read only through E5-D, never as R-H2.

## Non-matrix manipulation gates

All three gates ran at `a6d1116` with a clean tree, at non-matrix seeds, and their records are pinned.

| Gate | Record SHA-256 | Result |
|---|---|---|
| **P5 inertness** | `18f927a9…c569c` | **PASS.** 40 pairings, covering every pairing in which an inferring fixture meets a matrix opponent, including four mirrors, were each played at seeds 101–104 under T-E5's Ruleset. For each, the frozen fixtures were compared with test-only offset-aware copies, whose only change corrects the anchor-derived enemy-core adoption by their own spawn offset. All 160 comparisons are byte-identical. The −2 sensitivity case (a scoped patch placing the spawn at `pc − 2`, seed 101) detects a difference in **40 of 40**. The eight offset-aware copies' SHA-256 values are in the record. |
| **Observation delta** | `29049fbd…9cf` | **PASS.** 49 pairings (F1 both orders and the F2 mirrors) × seeds 101–102 × both treatment Rulesets gave 196 comparisons of each seat's first observation with its parent's, with 0 failures. The only differences are `self_anchor` and every visible enemy anchor, at −1. The −2 shift is accepted in **0 of 49** sensitivity cases. |
| **D9 real fixture** | `b0917709…437f1` | **PASS.** E3's D9 scenarios ran unchanged under T-E5's Ruleset: the repair and disrupt guards, both seats, 11 adversaries and seeds 42, 1001 and 1002, 132 scenarios in all, with **0 guard completions**. The whole-tick E2 Ruleset (sensitivity) captures the repair guard in 60 scenarios. |

## Treatment unlock (verification only)

`run_e5 unlock` returns `{"unlocked": true}` at `acba511`, with a clean tree. It executes nothing. It re-verifies:
- the committed freeze and its control qualification;
- the SHA-256 of all five control records and of every qualified control telemetry file;
- parent reproduction, the relabel gate and analyzer qualification;
- the three non-matrix gates;
- the populations, which it recomputes from the control corpus and requires to be identical;
- every pre-treatment hard stop: control census, control-side E5-D, the global-null signature and O-MIN-SB.

An unlocked state means only that a separately authorized treatment run would be permitted by the instrument. It has not been run.

## Mutation testing

Each mutation was applied to one committed file: the frozen E5 tooling, or for E1–E4 the engine. The E5 test modules were then run: the engine-side E5 modules for E1–E4, and the six tooling modules plus the guard modules for the rest.

- **Restoration.** Each file was restored byte for byte from `HEAD`, and `HEAD` and a clean tree were verified before the next mutation. Nothing was committed from a mutated tree.
- **Classification.** Every failing test was classed by its failure reason.
  - Any tooling edit also trips the freeze's own drift check (`AnalysisFreezeError`: "tooling files changed since the freeze", or a pinned-SHA mismatch). A failure caused only by that check, including the two committed-freeze tests, is **not** counted as behavioural detection.
  - A mutation is "detected" only if at least one test fails for a behavioural reason.

**Round 1** ran at `4d889e0`, against the tests as committed at the control qualification. **39 of 54** mutations were detected behaviourally. The other 15 (M4, M5, M18, M21, M25, M31, M34, M35, M36, M38, M40, M41, M42, M44 and M50) were refused only by the freeze's drift check. None went entirely undetected, but for those 15 no test exercised the guarded behaviour.

- **Harness defect (fixed).** A first pass of round 1 wrongly counted M41 and M42 as behavioural. Its runner passed a second `-q` on top of `pytest.ini`'s, which suppressed the failure reasons. With the reasons restored, the one test failing under M41 and M42 (`test_execute_needs_confirmation…`) failed on the drift error, not on the refusal. Round 1 was rerun in full with the corrected harness, and the figures above are from that rerun.
- **Weak detection of M10.** M10 (pooling raw ticks across seeds) was detected only by a `KeyError`: the per-seed-median guard's fixture lacked tick counts.

**The gaps were closed by tests only** (`acba511`: `test_v6_e5_mutation_guards.py`, and tick counts added to the guard fixture). No tooling file changed, and the freeze identity is unchanged.

**Round 2** ran at `acba511`: **all 54 detected behaviourally**. M10 now fails on its value (the pooled unit reads 1/26, neutral, against the per-seed median 1, second-strong). After every restore the file equalled `HEAD` byte for byte, the tree was clean, and `HEAD` was unchanged.

| # | Mutation | File | Round 1 (`4d889e0`) | Round 2 (`acba511`): failing behavioural tests (count) |
|---|---|---|---|---|
| M1 | BP sign flipped (first minus second) | `cell_metrics.py` | behavioural | `test_anchor_only_contest_under_the_parent_is_carried_by_anchor_hits`, `test_parity_value_is_the_exact_second_minus_first_share`, … (3) |
| M2 | BP parity assignment swapped (victim's own first-mover ticks used as its second-mover ticks) | `cell_metrics.py` | behavioural | `test_anchor_only_contest_under_the_parent_is_carried_by_anchor_hits`, `test_sweep_backed_opening_contest_under_the_parent` (2) |
| M3 | Base read from the tick-0 anchor instead of the recorded pc | `cell_metrics.py` | behavioural | `test_dual_counts_a_hit_on_a_process_that_moved_onto_its_own_core`, `test_the_base_is_the_recorded_pc_never_the_anchor`, … (8) |
| M4 | Cell DECIDED_EARLY off by one (> 10 both-alive ticks instead of ≥ 10) | `cell_metrics.py` | **freeze drift only** | `test_bp_is_defined_from_exactly_ten_both_alive_ticks_per_parity` (1) |
| M5 | DUAL counts only default-anchor dual writes (D-3 measurement narrowed) | `cell_metrics.py` | **freeze drift only** | `test_dual_counts_a_hit_on_a_process_that_moved_onto_its_own_core` (1) |
| M6 | Spawn mode reads pc + 1 as before_core (D-1 measurement) | `cell_metrics.py` | behavioural | `test_dual_counts_a_hit_on_a_process_that_moved_onto_its_own_core`, `test_treatment_manipulation_quantities_only` (7) |
| M7 | Band edge 1/3 made open (BP = 1/3 read as neutral) | `analyze_e5.py` | behavioural | `test_bp_band_edges_are_exact_and_closed_away_from_neutral` (1) |
| M8 | Unit DECIDED-EARLY rule off by one (exactly half defined → DECIDED-EARLY) | `analyze_e5.py` | behavioural | `test_a_unit_is_decided_early_with_fewer_than_half_defined_cells` (1) |
| M9 | Unit value is the mean of per-seed values, not the median | `analyze_e5.py` | behavioural | `test_the_unit_value_is_the_median_of_per_seed_values_never_pooled_ticks` (1) |
| M10 | Unit value pools raw ticks across seeds (directed units) | `analyze_e5.py` | behavioural | `test_the_unit_value_is_the_median_of_per_seed_values_never_pooled_ticks` (1) |
| M11 | Transition precedence: the STAYS test removed (same band falls through to STRENGTHENED) | `analyze_e5.py` | behavioural | `test_a_control_against_itself_is_always_an_identity_class`, `test_every_band_pair_maps_to_exactly_one_class`, … (5) |
| M12 | NEUTRALIZED and FLIPPED swapped | `analyze_e5.py` | behavioural | `test_every_band_pair_maps_to_exactly_one_class` (6) |
| M13 | WEAKENED removed from the E5-H1 numerator | `analyze_e5.py` | behavioural | `test_census_values_and_the_decided_early_denominator`, `test_h1_and_h2_numerators_are_disjoint_second_side_classes` (2) |
| M14 | WEAKENED also counted toward E5-H2 (numerators overlap) | `analyze_e5.py` | behavioural | `test_census_values_and_the_decided_early_denominator`, `test_h1_and_h2_numerators_are_disjoint_second_side_classes` (2) |
| M15 | NEITHER read as REFUTED | `analyze_e5.py` | behavioural | `test_census_values_and_the_decided_early_denominator`, `test_decided_early_units_stay_in_the_hypothesis_denominator`, … (7) |
| M16 | SUPPORTED threshold made strict (2/3 exactly → NEITHER) | `analyze_e5.py` | behavioural | `test_status_thresholds_are_inclusive` (1) |
| M17 | Impossible-combination check removed from interpret | `analyze_e5.py` | behavioural | `test_both_supported_is_an_invariant_violation`, `test_every_status_combination_maps_to_exactly_one_outcome_or_fails_closed` (18) |
| M18 | Interpretation: first matching row wins (arbitrary precedence over overlapping rows) | `analyze_e5.py` | **freeze drift only** | `test_interpret_never_resolves_an_overlap_by_row_order` (1) |
| M19 | Simultaneous H1/H2 SUPPORTED resolved by precedence (read as H1) | `analyze_e5.py` | behavioural | `test_both_supported_is_an_invariant_violation`, `test_every_status_combination_maps_to_exactly_one_outcome_or_fails_closed` (4) |
| M20 | A non-census class in SB P-BASE silently tolerated | `analyze_e5.py` | behavioural | `test_a_non_census_class_in_p_base_fails_closed` (1) |
| M21 | DECIDED-EARLY units dropped from the E5-H1/H2 denominator | `analyze_e5.py` | **freeze drift only** | `test_decided_early_units_stay_in_the_hypothesis_denominator` (1) |
| M22 | Contest class ignores the control inference audit (sweep role alone → SB) | `analyze_e5.py` | behavioural | `test_directed_class_follows_the_sweep_role_and_the_control_audit` (4) |
| M23 | An incorrect inference counted toward SWEEP-BACKED | `analyze_e5.py` | behavioural | `test_directed_class_follows_the_sweep_role_and_the_control_audit` (1) |
| M24 | Mirror unit value takes one victim instead of the mean of both | `analyze_e5.py` | behavioural | `test_a_mirror_cell_is_the_mean_of_its_two_victims` (1) |
| M25 | MIXED-INFERENCE units counted into the SWEEP-BACKED census | `analyze_e5.py` | **freeze drift only** | `test_mixed_inference_units_never_enter_the_sweep_backed_census` (1) |
| M26 | E5-D: D-1 (spawn = pc − 1) check removed | `gates.py` | behavioural | `test_each_decoupling_clause_fails_on_its_violation` (2) |
| M27 | E5-D: D-3 (DUAL = 0) check removed | `gates.py` | behavioural | `test_each_decoupling_clause_fails_on_its_violation` (1) |
| M28 | E5-D: D-5 (treatment side) ignores anchor-induced core-0 contact | `gates.py` | behavioural | `test_the_contest_check_catches_anchor_induced_contact_in_an_anchor_only_unit` (1) |
| M29 | E5 metrics dropped from the parent reproduction comparison | `gates.py` | behavioural | `test_the_parent_comparison_also_compares_e5_metrics` (1) |
| M30 | D9 stop ignored under T-E5 | `gates.py` | behavioural | `test_require_decoupling_and_d9_stop` (1) |
| M31 | O-MIN-SB weakened in build_record (5 SWEEP-BACKED units pass) | `populations.py` | **freeze drift only** | `test_build_record_computes_the_minimum_sweep_backed_halt` (1) |
| M32 | O-MIN-SB HALT ignored by require_ready | `populations.py` | behavioural | `test_fewer_than_six_sweep_backed_units_halts_before_treatment` (1) |
| M33 | Control-vs-control global-null signature check removed | `populations.py` | behavioural | `test_the_control_against_itself_must_read_as_the_null_caught_by_e5_d` (3) |
| M34 | Control-side D-5 check removed | `populations.py` | **freeze drift only** | `test_control_d5_needs_anchor_induced_contact_in_every_defined_anchor_only_cell` (1) |
| M35 | D-6 check removed | `populations.py` | **freeze drift only** | `test_d6_needs_a_dual_write_wherever_an_unmoved_anchor_is_hit` (1) |
| M36 | Incorrect control inference not flagged | `populations.py` | **freeze drift only** | `test_an_incorrect_control_inference_is_flagged` (1) |
| M37 | Frozen-population recompute check removed | `populations.py` | behavioural | `test_frozen_populations_must_recompute` (1) |
| M38 | Control-vs-control hypotheses evaluated with E5-D PASS (the null would read R-H2) | `populations.py` | **freeze drift only** | `test_build_record_computes_the_minimum_sweep_backed_halt` (3) |
| M39 | e2_counter re-admitted to the E5 field | `matrix.py` | behavioural | `test_exclusions_are_exactly_the_four_decided_ones`, `test_matrix_definition_is_frozen` (2) |
| M40 | Ruleset registry drift (more than one differing field) ignored | `matrix.py` | **freeze drift only** | `test_a_drift_outside_the_registered_parameters_breaks_the_one_field_difference` (1) |
| M41 | execute runs without --confirm-matrix-execution | `run_e5.py` | **freeze drift only** | `test_execute_refuses_before_reading_the_freeze` (1) |
| M42 | A treatment runs without its separate confirmation | `run_e5.py` | **freeze drift only** | `test_execute_refuses_before_reading_the_freeze` (1) |
| M43 | Treatment telemetry not detected as a treatment artifact | `run_e5.py` | behavioural | `test_treatment_telemetry_is_a_treatment_artifact_too` (1) |
| M44 | Unlock ignores a changed control record (SHA not compared) | `run_e5.py` | **freeze drift only** | `test_the_unlock_compares_every_control_record_sha` (1) |
| M45 | Offset-aware copy leaves the core adoption uncorrected (identical to the frozen fixture) | `nonmatrix_gates.py` | behavioural | `test_the_offset_aware_copy_changes_only_the_core_adoption` (1) |
| M46 | P5 passes without a detecting −2 sensitivity case | `nonmatrix_gates.py` | behavioural | `test_the_p5_gate_needs_identity_and_a_detecting_sensitivity_case` (1) |
| M47 | P5 sensitivity patch uses the treatment's own −1 (cannot detect) | `nonmatrix_gates.py` | behavioural | `test_the_p5_sensitivity_case_really_moves_the_spawn` (1) |
| M48 | Observation gate ignores a wrongly accepted −2 shift | `nonmatrix_gates.py` | behavioural | `test_the_observation_gate_needs_every_delta_and_a_rejected_shift` (1) |
| M49 | Non-matrix gates allowed on matrix seeds | `nonmatrix_gates.py` | behavioural | `test_non_matrix_gates_refuse_matrix_seeds` (1) |
| M50 | D9 gate passes without its whole-tick sensitivity capture | `nonmatrix_gates.py` | **freeze drift only** | `test_the_d9_gate_needs_its_whole_tick_sensitivity_capture` (1) |
| E1 | before_core spawns on core cell 0 (manipulation absent) | `ruleset_policy.py` | behavioural | `test_a_default_spawn_inside_an_adjacent_core_fails_closed`, `test_a_process_may_move_onto_its_own_core_and_be_dual_hit_there`, … (67) |
| E2 | before_core spawns at d = −2 | `ruleset_policy.py` | behavioural | `test_a_default_spawn_inside_an_adjacent_core_fails_closed`, `test_a_process_may_move_onto_its_own_core_and_be_dual_hit_there`, … (36) |
| E3 | Default-spawn-in-core validation removed | `match_service.py` | behavioural | `test_a_default_spawn_inside_an_adjacent_core_fails_closed` (4) |
| E4 | Runtime ignores the Ruleset's spawn rule (always core cell 0) | `process_runtime.py` | behavioural | `test_a_process_may_move_onto_its_own_core_and_be_dual_hit_there`, `test_an_explicit_initial_position_is_kept`, … (37) |

The mutations and their failure reasons for both rounds are kept with this phase's working notes (not committed). The mutations were chosen to break each registered rule:
- the BP formula, its parity, base and DECIDED-EARLY boundary;
- the per-seed median;
- band closedness and transition precedence;
- the H1/H2 numerators and denominator;
- NEITHER versus REFUTED;
- the impossible and overlap handling;
- the contest classification and MIXED exclusion;
- every E5-D clause on both sides;
- O-MIN-SB;
- the global-null signature;
- the recompute and SHA checks;
- the runner's refusals and artifact detection;
- the three non-matrix gates' sensitivity conditions;
- the manipulation itself.

## Tests

| Module | Tests | Covers |
|---|---|---|
| `test_v6_e5_parent_byte_identity.py` | 98 | 96 matches under both parent Rulesets (8 E5 pairings × 2 orientations × seeds 1–3), recorded against the unmodified runtime at `4fbd1d4` and committed at `8f6717d` before any placement change, plus the anchors digest: the `core_base` path reproduces them byte for byte |
| `test_ruleset_v6_research_anchor_before_core.py` | 84 | The two Rulesets' policy, identity, one-field difference, strict validation and registration; the default-spawn-in-core guard; evaluation plumbing; product isolation; determinism; serialization (replay and result shape unchanged) |
| `test_e5_anchor_placement_semantics.py` | 44 | Spawn at `pc − 1`; an explicit position is kept; no movement prohibition (a MOVE onto the own core is DUAL-hit there); DUAL = 0 and no own-core occupancy for the research fixtures; the observation delta; G.4/G.5; opening-pass traces |
| `test_v6_e5_analysis.py` | 113 | O-BP, bands and edges, unit medians and DECIDED-EARLY, mirror values, every band pair to exactly one class, precedence, statuses, NEITHER ≠ REFUTED, the census, every (E5-D, H1, H2) combination to exactly one outcome or a fail-closed impossibility, the table-totality loader, contest classification |
| `test_v6_e5_cell_metrics.py` | 12 | Real replays: SB and AO contests under the parents; the treatment manipulation quantities only (blindness); spread fixtures' own-core occupancy; DECIDED_EARLY; reconstruction disagreement; the base is `pc`, never the anchor |
| `test_v6_e5_matrix.py` | 15 | The frozen definition and counts, exclusions, sweep roles, conditions and one-field difference, registry drift, historical generation, the pre-registration digest and tamper, confirmations, treatment-artifact STOP, forbidden overrides, the dry run |
| `test_v6_e5_gates.py` | 27 | E5-D D-1 to D-5 treatment side, D9 stop, the E5 parent comparison, the populations' hard stops (O-MIN-SB, control clauses, census, global null, recompute), the offset-aware copy, the non-matrix gates' seeds, spawn patch and observation delta |
| `test_v6_e5_freeze.py` | 10 | The separate freeze identity; drift and reused-file pinning; the unlock chain; the committed freeze; the committed control qualification and populations |
| `test_v6_e5_instrument_guards.py` | 8 | The per-seed median (never pooled ticks); the P5 and observation gates' pass conditions |
| `test_v6_e5_mutation_guards.py` | 25 | The round-1 gaps (see Mutation testing) |

**Full suite** at `acba511`: 4,658 passed, 18 skipped, 3 deselected, 0 failed (11 min 10 s). At the analysis freeze `aab8fa4`, the suite gave 4,623 passed and 1 failed; the failure is a pre-existing timing flake outside E5 (limitation 7).

## Treatment-Ruleset exposure in this phase

No matrix seed (1–32) has run under a treatment Ruleset. No T-E5 or T-E5K1 directory, cell or telemetry exists. Since the Rulesets were implemented, no treatment BP value has been written to any record, asserted by a test or read. `cell_metrics` computes BP in memory for every replay it is given, and the treatment-replay tests discard it. Separation was run only in the following places, each outside the matrix.

- **Design review probe, before any E5 Ruleset existed.** The preserved design review discloses this exposure itself, under "Probe exposure".
  - **What it ran.** A scratch patch moved every initial anchor to `core_base − 1` after controller construction. The runs covered named scenarios at seeds 42 and 1001–1003.
  - **What the review reports.** It prints the resulting [PROBE] values as priors to be falsified. These include separated FMA and BP values for probed units; for example, its E5-H2 prior reads "every SB unit probed: BP 1.0 → 1.0, or 0.5 → 0.5".
  - **Standing.** The review states that no threshold came from them. The thresholds reuse E4's structural constants. They are not treatment data and are not part of this record's evidence.
- **Engine tests** (`test_ruleset_v6_research_anchor_before_core.py`, `test_e5_anchor_placement_semantics.py`) at seeds 42, 7 and 1. They cover spawn semantics, DUAL and own-core-occupancy characterizations over 30–60 ticks, the observation delta, G.4 and short opening-pass traces.
  - **G.5.** This test runs full 1,000-tick treatment matches at seed 42 (repair or disrupt guard against each sweeper, both seats) and reads only the guards' kill events, which is the theorem.
  - **Replay/result shape.** This test runs the guarded-painter mirror for 200 ticks at seed 7 under each treatment. Its comment records that the mirror ends by capture under K = 1 in both arms, a precondition for exercising the kill-event shape.

  These are mechanical characterizations at non-matrix seeds, not census inputs.
- **`test_v6_e5_cell_metrics.py`** at seed 7. Under a treatment it reads only the manipulation quantities: spawn mode, D-2, DUAL and own-core occupancy.
- **`test_v6_e5_mutation_guards.py`**, with two test-only synthetic agents (a mover and a hitter) for 20 ticks. It reads only the D quantities.
- **The P5, observation-delta and D9 gates** described above, at seeds 101–104, 101–102, and 42, 1001 and 1002. They record identity comparisons, first observations and guard completions only. Smoke runs of the same gate code during implementation (40 of 40 identical, with the −2 case detected 40 of 40; 98 observation comparisons with 0 wrong acceptances) used the same non-matrix seeds and recorded nothing.

## Limitations recorded before treatment (control data only; nothing changed)

1. **Evidence weight.**
   - 13 of the 17 SWEEP-BACKED units are seed-invariant under the control (n_distinct = 1). Each of them is one characterization, not 32 observations.
   - Only 4 SB units are rate-claim eligible (n_distinct ≥ 8).
   - The E5-H1 and E5-H2 census criteria are therefore counts of unit characterizations, as registered, not rates.
2. **The thresholds in whole units.** With N = 17 frozen:
   - SUPPORTED needs at least 12 units in the numerator;
   - REFUTED needs at most 1;
   - 2 to 11 units reads NEITHER, which is never REFUTED.
3. **A seed-invariant SB population.** 13 SB units have control BP exactly 1: the victim owns its base at the end of every one of its second-mover ticks and none of its first-mover ticks. For these units STAYS needs a treatment unit BP of at least 2/3, and any median below 2/3 reads WEAKENED, NEUTRALIZED or FLIPPED.
4. **D-3 on control data.** In all 3,584 control cells, DUAL equals the default-anchor dual writes: no control dual write hit a process that had moved. The non-default branch of D-3 is exercised only by a synthetic test (above). Under treatment, D-3 and D-4 are E5-corpus characterizations, not Ruleset invariants: a fixture may still MOVE onto its own core.
5. **P5 is a non-matrix gate.** The review argues inertness for the four list-first sweepers (its §F, P5), and the gate confirmed it byte for byte at seeds 101–104 over every inferring pairing, as registered. It is not re-checked at the matrix seeds, whose treatment cells do not exist.
6. **Clean-export reproducibility** (done for E4) was not repeated for E5.
7. **A pre-existing flake.** The full suite at `aab8fa4` had one failure outside E5: `test_agent_validation.py::test_supervised_reset_timeout_is_reported` reported `agent_load_timeout` for `agent_reset_timeout` under load, with a 1.0 s budget covering module load and reset. It passed in isolation 6 of 6 and 5 of 5, and in the full suite at `acba511`. No commit of this phase touches agent validation.

## What a treatment authorization would unlock

Nothing below has been run. It needs separate authorization.

```
python -m tools.research.v6.e5.run_e5 execute T-E5   F1 --confirm-matrix-execution --confirm-treatment-execution --workers 1
python -m tools.research.v6.e5.run_e5 execute T-E5   F2 --confirm-matrix-execution --confirm-treatment-execution --workers 1
python -m tools.research.v6.e5.run_e5 execute T-E5K1 F1 --confirm-matrix-execution --confirm-treatment-execution --workers 1
python -m tools.research.v6.e5.run_e5 execute T-E5K1 F2 --confirm-matrix-execution --confirm-treatment-execution --workers 1
python -m tools.research.v6.e5.run_e5 treatment-telemetry T-E5   --workers 12
python -m tools.research.v6.e5.run_e5 treatment-telemetry T-E5K1 --workers 12
python -m tools.research.v6.e5.run_e5 treatment-gates T-E5
python -m tools.research.v6.e5.run_e5 treatment-gates T-E5K1
python -m tools.research.v6.e5.run_e5 analyze
```

Each treatment execution re-runs the full unlock chain before its first cell. The treatment gates apply E5-D (D-1 to D-5), the manipulation checks and the D9 stop before `analyze` will read any BP.

## What this record does not claim

- It makes no E5 gameplay claim and predicts no E5 result. Every registered reading, including STOP and "no row applies", stays reachable.
- It does not claim that co-location is or is not necessary. That is the question the treatment would answer.
- It does not claim inertness of the excluded fixtures. They were excluded because the −1 offset is not inert for them.
- It reinterprets no E2, E3 or E4 freeze, pre-registration, corpus or result. E4's records are read only, through their pins.
