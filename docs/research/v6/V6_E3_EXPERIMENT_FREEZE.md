# Bytefray V6 E3 — Slot-Limited Disruption: Research Tooling, Pre-registration and Experiment Freeze

**Status:** The E3 research tooling is built and qualified. The experiment is frozen, and both controls (C-E2, C-RS) have been run and qualified. **Neither treatment condition (T-E3, T-E3K1) has been run.** Nothing in this record is a gameplay result, and no E3 conclusion is drawn.
**Branch:** `v6-research`. Baseline `be6c64e08a48d763e88c9dc1516ed2f1755b773f`; tooling qualified at `d1f69b98c6721e08d7d3eba6bc7989c9de07a4dd`; analysis freeze committed at `b8ac343c66b7827a3b5c40971c072eae49aa737f`.
**Authority:** [`V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md`](V6_E3_SLOT_LIMITED_DISRUPTION_DESIGN_REVIEW.md) (§J populations, hypotheses and interpretation; §K metrics; §L matrix; §M evidence rules; §N qualification, freeze and hard stops). The Rulesets are recorded in [`V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md`](V6_E3_SLOT_LIMITED_DISRUPTION_REGISTRATION.md) and are unchanged by this phase.

## Scope

This phase carries out the review's §N steps 3 to 6:

- it builds the research tooling: the jam fixture and its twin, and an action/parity analyzer;
- it qualifies that tooling on control data only;
- it freezes the matrix identity and, separately, the analysis identity;
- it runs the two controls and passes them through the parent reproduction gate.

It stops before §N step 7. The treatment is separately authorized and was not run.

No gameplay code changed. `engine/src` is byte-identical to the qualified E3 implementation (tree `67b73c9ae7d40209ef68e9512a58c5adfef0ac2f`, commit `75ed578`). No replay, result or schema changed. The E2 instrument, including capture analyzer v2, the experiment harness and E2's committed freeze `v6-e2-freeze-v2-db6458596d82`, is reused byte for byte, and it still loads and verifies.

## Where things live

| Path | Contents |
|---|---|
| `tools/research/v6/e3/fixtures/agents/` | `e3_jam_sniper` and `e3_jam_sniper_twin`, with a fingerprint table in the directory's `README.md` |
| `tools/research/v6/e3/entrants.py` | Resolves E3 entrants from tracked sources. The frozen harness is not edited. |
| `tools/research/v6/e3/matrix.py` | The frozen experiment definition and its digest |
| `tools/research/v6/e3/preregistration.json` / `preregistration.py` | D0–D9 and the rules around them, verbatim, plus the operationalizations. The digest is pinned. |
| `tools/research/v6/e3/action_parity.py` | The E3 analyzer, version 1: PM-1, the PM-2 category, MC-1, MC-2, exposure and the first hit |
| `tools/research/v6/e3/analyze_e3.py` | Populations, PM-1 to PM-4, the MC summaries, the §M rule 4 residual rule, the control baseline, and the D0–D9 criteria |
| `tools/research/v6/e3/gates.py` | Parent reproduction, the prefix gate, the F2-P prefix check, the manipulation checks and the D9 stop check |
| `tools/research/v6/e3/telemetry.py` | Per-cell telemetry for a whole corpus (process pool, JSONL, repeatability digests) |
| `tools/research/v6/e3/populations.py` | The frozen control populations and the control baseline |
| `tools/research/v6/e3/d9_gate.py` | The D9 real-fixture gate |
| `tools/research/v6/e3/analysis_freeze.py` / `analysis_freeze.json` | The analysis freeze identity and its committed record |
| `tools/research/v6/e3/control_populations.json` | The frozen exposed, stalemate and hit-free cell identities, and the control baseline |
| `tools/research/v6/e3/run_e3.py` | The runner: `plan`, `execute`, `telemetry`, `reproduce`, `qualify`, `populations`, `d9`, `unlock`, and, for after authorization, `treatment-telemetry`, `treatment-gates` and `analyze` |

## The jam fixture

The review's §L and §O-4 name exactly one new agent, and E3 has only that one. Every E2 fixture hits each enemy anchor at most once per tick. Without a jammer, the maximal-denial regime would never be exercised, and neither would D6.

**`e3_jam_sniper`** has one global-reach process. Within each tick it alternates, according to its own action count in that tick:

- even actions (0, 2, 4 and 6) write a visible enemy anchor, a disruptive hit;
- successive hits in one tick cycle through the visible anchors;
- odd actions (1, 3, 5 and 7) write the next enemy core cell, from a cursor over core offsets 1 to size−1 that continues across ticks.

Offset 0, the core base, is where every enemy spawns, and the hits cover it. A hit with no visible anchor becomes a core write. A core write before the enemy core is known becomes a hit. With neither, the agent reads its own core base, which has no effect.

The agent follows the E2 fixture contract:

- Agent API v2;
- public information only;
- the single-location enemy-core inference rule;
- no randomness.

It is a diagnostic stressor. It was not tuned to win the field.

**`e3_jam_sniper_twin`** has a byte-identical `agent.py`. Its manifest differs only in `name` and `display`.

| Fixture | Fingerprint (`agent_revision_fingerprint`) |
|---|---|
| `e3_jam_sniper` | `f92c056e271ce16492119fd57edf7ce10985f3aef88636228f8c7434a1a7ad8e` |
| `e3_jam_sniper_twin` | `6035dd549edf49bbd0a62f5713a797fc268e2edb9e20a7b9e96d71dc159a31e2` |

The behaviour is asserted from canonical replays at seed 42, which is outside the matrix (`test_v6_e3_fixtures.py`).

- **Under the whole-tick parent.** Against the repair guard, tick 1 writes 203, 204, 203, 205, 203, 206, 203, 207: four hits and four core writes. The cursor continues at offset 5 on tick 2 and wraps to offset 1. The twin plays identically, and repeated runs are byte-identical.
- **Under λ = 1.** The opponent is a scripted, non-matrix victim that only idles. The alternation holds it to exactly the G.4 minimum, 4 actions as second mover and 5 as first mover. This is repeated finite suppression inside one tick, the regime the fixture exists to exercise.

## The action/parity analyzer

`action_parity.analyze_actions` reads one canonical replay and its `result.json`. It needs no new replay field. It reuses capture analyzer v2 unchanged, by import, and never re-derives capture state. PM-1 needs per-tick core ownership, which the capture analyzer does not expose. The E3 analyzer therefore rebuilds ownership with the capture analyzer's own address helper, and on every replay it requires that each entrant's zero-core evaluation ticks and final owned count equal capture analyzer v2's. A difference is reported as a capture-analyzer disagreement.

| Metric | Definition (operationalization) |
|---|---|
| **PM-1** FMS / PD | Core balance b(t) is Seat A's owned own-core cells minus Seat B's at the end of tick t. A swing tick is one where both entrants are alive at the end of t and b(t) ≠ b(t−1). The swing favours the first mover, which is seat (t−1) mod 2. FMS is the share of swings that favour the first mover, and PD = \|2·FMS − 1\|. Scoring needs ≥ 10 swings. Otherwise the cell is `NOT_SCOREABLE`, which is counted and reported, never dropped. The direction is `neutral_weak` (PD ≤ 0.5), `first/last_mover_dominated` (PD ≥ 0.9), or `…_leaning` in between (O-FMS). |
| **PM-2** phase-lock | Capture analyzer v2's phase-lock, per entrant. `NO_ZERO_CORE_TICKS` is a category, never a phase-lock of 0. Otherwise the category is `PHASE_LOCK_AVAILABLE`, reported with the two-sided reading \|2·PL − 1\| and a direction (O-PHASE-LOCK). |
| **MC-1** executed actions | Per live entrant per tick: Q = 8 nominal offers, executed = `cpu_used`, and first- or second-mover status. The analyzer also reports the exclusive-tick share (both entrants alive at the end of the tick, one executed 0) and G.4 violations for entrant-ticks alive throughout (fewer than 5 as first mover, fewer than 4 as second). Σ `cpu_used` must equal `result.json` `statistics.cpu_total`. |
| **MC-2** ADF | (Q − executed) / Q, for entrants alive at the end of the tick with no forfeit in it, reported by role, by entrant and by pairing |
| Exposure | Some entrant that was offered actions in a tick and did not forfeit executed fewer than 8. By the review's §C proof, for the matrix agents this is exactly an offer lost to disruption (O-EXPOSED). |
| First hit | The first tick in which any process carries the replay's `disrupted` flag (for the prefix gate) |

**Reproducing the review's corpus facts** (on the preserved T-E2 corpus, with no threshold involved):

- F1: 1,002,240 exclusive ticks of 1,602,067 both-alive ticks (62.6%), and a second-mover mean of 2.752 executed actions. The review gives 62.6% and 2.75.
- All 2,880 F1 cells contain a hit, and exactly 64 of the 640 F2 cells contain none, as the review states.
- F2: 59.1% and 0.913. The review gives 59.1% and 0.91. These F2 figures are over the 576 hit-bearing cells. Over all 640 cells, including the 64 hit-free repair-guard mirror cells, the values are 49.4% and 2.077. The review's F2 denominator is therefore the hit-bearing cells, and that has been recorded, not changed.

## Frozen experiment definition

`matrix.py`, digest `634132ec3c15549b8032b7414c2a0f649ff2e3a754f592c5c2a71090b37215e8`, **matrix id `v6-e3-matrix-v1-634132ec3c15`**.

| Condition | Ruleset | K | λ | Role |
|---|---|---|---|---|
| C-E2 | `bytefray-rules-6-research-capture-hold-k2` | 2 | None | Primary control; parent of T-E3 |
| T-E3 | `bytefray-rules-6-research-capture-hold-k2-disruption-slot1` | 2 | 1 | Primary treatment |
| C-RS | `bytefray-rules-6-research-scale` | 1 | None | Companion control; parent of T-E3K1 |
| T-E3K1 | `bytefray-rules-6-research-disruption-slot1` | 1 | 1 | Companion treatment |

On every load the registry is re-checked, and each treatment must differ from its parent only in `disruption_slot_limit` (and its id).

| Field | Composition | Pairs | Ticks | Per condition |
|---|---|---|---|---|
| F1 | E2's triangular round robin of the ten E2 agents, unchanged | 45 | 1000 | 2,880 |
| F2 | E2's ten agent/twin mirrors | 10 | 1000 | 640 |
| F2-P | F2 at 1001 ticks, so the tick-limit tick belongs to the other seat's parity | 10 | 1001 | 640 |
| F4 | `e3_jam_sniper` against each of the ten E2 agents, plus the jam mirror | 11 | 1000 | 704 |

- **Totals.** 4,864 matches per condition. The primary study (C-E2 and T-E3) is 9,728 matches, and the full experiment is **19,456**. The real evaluation planner's dry run plans exactly 19,456 cells, with every condition and field consistent in Ruleset, tick limit, seeds and orientations.
- **Fixed settings.** Arena 512; seeds 1–32, given explicitly; both orientations; no K = 3 arm. All four request overrides (`scheduler_chunk_size`, `scheduler_rotate_start`, `kill_weight`, `instr_per_tick`) must be `None` on the exact requests that run, and the runner fails closed otherwise.
- **F3 is dropped** (review §L). No replacement reference agents were added.
- **Fingerprints.** The definition freezes the fingerprints of all 22 entrants. The twenty E2 values are E2's frozen ones.
- **Historical parents.** For each control and each field with a historical counterpart (F1, F2), the definition names the preserved E2 corpus the control must reproduce. C-E2 must reproduce E2's T-E2, and C-RS must reproduce E2's C-RS.

**Guards on every execution** (`run_e3.execute`):

- an explicit `--confirm-matrix-execution`;
- the frozen matrix and pre-registration digests, and the registry check;
- the committed analysis freeze, still holding against the live tooling;
- a clean tree whose `engine/src` is the frozen tree, and whose tooling files equal their content at the tooling commit, checked before and again after the run (hard stop 10);
- live fingerprints equal to the frozen ones;
- request checks on the planned requests, both before anything is written and inside the harness;
- the exact cell count;
- refusal to run a cell set whose output directory already exists;
- for every control, a STOP if any treatment artifact exists.

A treatment additionally needs a separate `--confirm-treatment-execution` flag and the whole unlock chain described below. It has no sample mode.

## Hypothesis pre-registration

`preregistration.json`, SHA-256 **`2b5f82b4411efca561726e0e63a70fcfe24e5804b2b86b7eef7b71696cafbdd0`**, is pinned in `preregistration.py`, and loading fails closed on any change. It holds the following, verbatim from the review:

- D0–D9, each with its statement, supported-if and refuted-if clauses and probe prior;
- the interpretation table and "A clean negative is reachable.";
- the threshold rationale;
- the §J population definitions and the §K metric definitions;
- the seven §M evidence rules;
- the eleven §N hard stops.

Only markdown emphasis and code formatting are removed. `test_v6_e3_matrix.py` parses the preserved review (SHA-256 `c0d0f711…`) and asserts each of these sections equal to the file.

| ID | Statement | Supported if | Refuted if |
|---|---|---|---|
| D0 | No structural change | Outcome class unchanged in ≥ 0.90 of exposed cells and D2 refuted | < 0.90 |
| D1 | Parity lock decreases | Median two-sided PD ≤ 0.5 in the stalemate population | Median PD ≥ 0.9 |
| D2 | Seat determination decreases | At least half of the C-E2 seat-determined units (3 F1 pairings + probe, sniper and guarded-painter mirrors) fall below SDI 0.9, no new unit reaches it, and 1000 and 1001 agree | None falls |
| D3 | Defense no longer needs disrupt-first | At least half of the repair guard's C-E2 capture losses to {probe, sniper, spread sniper, counter} become non-losses | None do |
| D4 | First-mover control persists | Median first-mover swing share ≥ 0.9 and D2 refuted | Median ≤ 0.5 |
| D5 | Location/process-count exploit | Spread agents' win-or-draw rate against the 8 stacked agents rises ≥ 0.10 in both seat tables | Falls |
| D6 | Re-disruption recreates control | The jam sniper decisively beats a repair, disrupt or min guard in both seats | No such win |
| D7 | Draw-ification | Tick-limit share in exposed F1 rises ≥ 0.10 absolute | Rises < 0.10 or falls |
| D8 | Last-mover inversion | Median PD ≥ 0.9 and median first-mover share ≤ 0.1 | Median PD ≤ 0.5 |
| D9 | Hold × order immunity | T-E3: 0 completions against repair and disrupt guards (a theorem, so also a stop check); T-E3K1: > 0 | T-E3K1 also 0 |

| Result | Conclusion (pre-registered) |
|---|---|
| D1 ∧ D2 | Whole-tick disruption is load-bearing for scheduler-locked play |
| D2 ∧ D8 | Load-bearing for first-mover outcome determination, but parity control persists through the last position. The next study is in-tick order or the evaluation instant, which needs a scope decision. |
| (D4 ∨ D8) ∧ ¬D2 | Not load-bearing; the disruption line closes |
| D7 | Recorded as a pathology whatever else holds |

**Operationalizations.** Each fixes, before any treatment data exists, only what the review leaves open, and each is labelled in the file.

- **O-POPULATION-FIELDS.** The populations are taken over the standard fields F1, F2 and F4, each cell once. F2-P exists only for the §M rule 7 parity check. Its cells are frozen and reported as their own stratum and never pooled, so no mirror counts twice. D7 uses the F1 part, which it names.
- **O-EXPOSED and O-STALEMATE.** They define a live entrant and a lost offer, and a stalemate as a tick-limit cell with a recovery counted by capture analyzer v2.
- **O-UNIT.** Criterion values use the population's cells as the denominator (§M rule 2). Each carries n_distinct, the number of distinct (C key, T key) transitions (§M rule 1). A value resting on fewer than 8 distinct transitions is labelled a deterministic characterization. The distinct-weighted value is descriptive only. D3, D5 and D6 use the cell sets their statements name, restricted to exposed cells, and every excluded cell is counted.
- **O-FMS, O-PARITY-MEDIANS and O-PHASE-LOCK.** They give the PM-1 and PM-2 definitions above. D1, D4 and D8 are criteria on the same parity metric, so they use the same population, the stalemate population; D4 and D8 name none. The exposed-population medians are secondary readings.
- **O-OUTCOME-CLASS.** It defines the four PM-3 classes, with "other" reported.
- **O-MIRROR-PARITY.** A mirror's claim is its seat-determination status and favoured seat. A mirror whose claim differs between 1000 and 1001 ticks is labelled `TICK_LIMIT_PARITY_DEPENDENT` and is never reported as a robust seat effect.
- **O-D2, O-D3, O-D5, O-D6 and O-D9.** They pin the unit universe (F1 pairings and F2 mirrors, with F4 as a separate stratum), what "falls", "capture loss", "non-loss", "win-or-draw" (pooled over both spread agents, per seat) and "decisively beats" (a decisive-win majority in each seat) mean, and D9's victims and cells.
- **O-RESIDUAL.** It is the §M rule 4 procedure on top of E2's O-H2-SIGNIFICANCE. A residual counts only if n_distinct ≥ 8, its 95% bootstrap interval (1,000 distinct-trajectory resamples, seed 42) excludes 0, |R| ≥ 1/8, the pairing is not a dominance pairing, and the same pairing's C-E2 residual does not count under the same code. The C-E2 table is frozen with the populations.
- **O-COMPANION.** D0–D8 verdicts are read from the primary arm. The companion arm is computed with identical code and reported as the λ-only deconfounder, and it never replaces a primary verdict. D9 uses both arms, and the companion's guard completions are never a stop.
- **O-STATUS.** Each criterion is evaluated to SUPPORTED, REFUTED or NEITHER, with its evidence label. Verdicts are then read under the interpretation table.

No threshold was derived from probe, corpus or control outcomes. The control numbers in this record were computed after the thresholds were frozen, and none of them is used to set or adjust one.

## Statistical and evidence rules (implemented)

- **Unit.** The paired distinct transition. Rate claims need n_distinct ≥ 8; below that the harness label is `deterministic_characterization` (1) or `limited_distinct_trajectories` (2–7), and `rate_claim_eligible` is false.
- **Denominators.** The frozen exposed or stalemate cells, never all cells.
- **Parity.** Two-sided, with direction; `NOT_SCOREABLE` and `NO_ZERO_CORE_TICKS` are counted categories.
- **Residuals.** Secondary, and counted only under all four §M rule 4 conditions, with the control comparison run on the frozen C-E2 table. A pairing whose distinct trajectories one side wins every time is reported as dominance.
- **Mirrors.** The 1000- and 1001-tick claims must agree; a disagreement is labelled `TICK_LIMIT_PARITY_DEPENDENT`.
- **Bradley–Terry.** Seat conditioning, convergence handling, n_distinct and the deterministic labels are retained from the E2 harness, and the pooled table stays subordinate.
- **Control computation.** Every hypothesis quantity is computed on C-E2, and by the same rules on C-RS, and frozen before treatment (§M rule 6).

## Freeze identities

The two identities are kept apart.

| Identity | Value | Covers |
|---|---|---|
| Matrix | **`v6-e3-matrix-v1-634132ec3c15`** (`634132ec…37215e8`) | conditions, Rulesets and their (K, λ), fields, pairs, seeds, orientations, per-field tick limits, arena, fixture fingerprints, agent lists, the forbidden overrides, the historical parents, the dropped F3, and the counts |
| Analysis freeze | **`v6-e3-freeze-v1-506811e78ad8`** (`506811e7…a52a1dbb`) | the matrix id and digest; the pre-registration SHA-256; the action/parity analyzer (version 1, `86b1a557…c4f211`); the E3 analysis version (1); capture analyzer v2 (`b818f53e…2c18f86`, pinned to E2 freeze `v6-e2-freeze-v2-db6458596d82` and checked byte-identical on every load); the SHA-256 of all 20 tooling files, including the reused E2 modules and the E3 fixtures; the tooling commit `d1f69b98…`; and the match-generation tree `engine/src` = `67b73c9a…` |

The freeze record's `control_qualification` block lies outside the identity digest. It was added after the controls passed, and it pins the SHA-256 of the three control-phase gate records and of `control_populations.json`.

## Control execution

Both controls ran through `run_e3 execute CONDITION FIELD --confirm-matrix-execution` at `b8ac343` with a clean tree, one match worker each, and the two conditions in parallel processes. Each field passed the execution-source check before and after its run. A source manifest was taken before the runs, covering `HEAD`, `git status`, the index hashes of `tools/research/v6` and `engine/src`, and the SHA-256 of every E3 tooling file, capture analyzer v2 and the harness. It was identical after the runs.

| Condition | F1 | F2 | F2-P | F4 | Total | Wall clock (UTC) |
|---|---|---|---|---|---|---|
| C-E2 | 2,880 | 640 | 640 | 704 | 4,864 | 01:44:58–02:17:03 |
| C-RS | 2,880 | 640 | 640 | 704 | 4,864 | 01:44:59–02:10:30 |

The artifacts are under `runs/research_v6_e3/v6-e3-matrix-v1-634132ec3c15/{C-E2,C-RS}/{F1,F2,F2-P,F4}`, and every `result.json` and replay is preserved (git-ignored). No cell failed, and no cell was re-run. **No T-E3 or T-E3K1 directory exists.**

## Parent reproduction gate

**FULL PASS** (`parent_reproduction.json`, SHA-256 `fe1e302428b3246f4cfdc614e28ec9fa91ea8616bd2a1ef766e7b900da637602`). Each new control and its historical parent run under the same Ruleset id, so nothing is excused. The comparison covers:

- every harness cell field, including `match_id` and `result_id`;
- the whole `result.json`, apart from its per-execution `completed_at` and `occurrence_id`;
- the replay bytes, by SHA-256;
- the E3 telemetry, meaning capture analyzer v2's telemetry and the executed-action record.

| New control | Historical parent (`v6-e2-matrix-v1-9048907fdc3b`) | F1 cells | F2 cells | Mismatches |
|---|---|---|---|---|
| C-E2 | T-E2 (generated at `f4ad557`, `engine/src` `5b7495ee…`) | 2,880 / 2,880 | 640 / 640 | 0 |
| C-RS | C-RS (generated at `062feeb`, same tree) | 2,880 / 2,880 | 640 / 640 | 0 |

In all, 7,040 matched cells are byte-identical to the preserved E2 corpus. The historical corpus was generated from the engine tree before E3's `disruption_slot_limit` existed, and the new controls from the E3 implementation tree. This is the λ = None byte identity, confirmed at full matrix scale in both parents.

**Fresh controls (F2-P, F4).** These fields have no historical counterpart. For each control:

- **Corpus integrity** (E2's `corpus_integrity`, reused unchanged): the exact frozen cell set with no duplicates or extras; every cell completed with its artifacts; on-disk match directories equal to the recorded cells; the condition's Ruleset in every `result.json`; the frozen digests, freeze id, condition, field and fingerprints in `provenance.json`; and a generating commit whose `engine/src` is the frozen tree. PASS.
- **Clean telemetry** in every cell. PASS.
- **F2-P against F2.** No fixture reads the tick limit, so every F2-P replay equals the same condition's F2 replay through tick 1000, apart from the tick limit in the header. Where F2 ended earlier, the two are identical entirely. This holds for 640 / 640 cells under C-E2 and 640 / 640 under C-RS.
- **Determinism re-run.** Seeds 1 and 17 of F2-P (40 cells) and F4 (44 cells) were re-executed into a scratch root. They are byte-identical, replays and results, to the main corpus.

## Analyzer qualification (control data only)

**PASS** (`analyzer_qualification.json`, SHA-256 `bd9c0096879409ca944b1e1b77ac7bf548185e627b1f04ae05de13c4188f6dc3`). The E3 analyzer, and through it capture analyzer v2, ran over every control replay. A second, independent pass then recomputed every row.

| Corpus | Replays | Failures | `cpu_used` ≠ `cpu_total` | Capture-engine disagreements | Ownership disagreements | Attribution mismatches | Second-pass differences |
|---|---|---|---|---|---|---|---|
| New C-E2 (F1, F2, F2-P, F4) | 4,864 | 0 | 0 | 0 | 0 | 0 | 0 |
| New C-RS (F1, F2, F2-P, F4) | 4,864 | 0 | 0 | 0 | 0 | 0 | 0 |
| Historical T-E2 (F1, F2, F3) | 5,120 | 0 | 0 | 0 | 0 | 0 | 0 |
| Historical C-RS (F1, F2, F3) | 5,120 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **19,968** | **0** | **0** | **0** | **0** | **0** | **0** |

- **No-zero-core handling.** It is sensible throughout. For example, C-E2 F1 has 3,461 entrant readings in the `NO_ZERO_CORE_TICKS` category and 2,299 with a phase-lock; none of the former is ever read as a phase-lock of 0.
- **Parity.** In C-E2 F1, 1,835 cells are `NOT_SCOREABLE` and 1,045 are scored. Every one is counted.
- **Pinned files.** The SHA-256 of each qualified telemetry file is recorded, and the unlock re-verifies it.
- **Thresholds.** None was tuned from these outputs; the thresholds were frozen before the controls ran.

## Frozen control populations

`tools/research/v6/e3/control_populations.json`, SHA-256 **`878754a2c961062f822ecae2bd55c143a8e84ace4b5c3a8125cbb9e44ff2cb95`**, is committed and pinned in the freeze record. It is computed from the new controls after they passed reproduction, and the unlock recomputes it and requires exact equality. It is never recomputed from treatment data.

| Arm (control) | Field | Cells | Exposed | Stalemate | Hit-free |
|---|---|---|---|---|---|
| Primary (C-E2) | F1 | 2,880 | 2,880 | **610** | 0 |
| | F2 | 640 | 576 | **64** | **64** |
| | F2-P (own stratum) | 640 | 576 | 64 | 64 |
| | F4 | 704 | 704 | 64 | 0 |
| Companion (C-RS) | F1 | 2,880 | 2,880 | 0 | 0 |
| | F2 | 640 | 576 | 0 | 64 |
| | F2-P (own stratum) | 640 | 576 | 0 | 64 |
| | F4 | 704 | 704 | 0 | 0 |

- **The review's expectation is reproduced exactly.** The C-E2 stalemate population is **610 F1 + 64 F2**; F4 adds 64, all jam-sniper cells.
- **Hit-free cells.** There are **64**, the repair-guard mirror in both orientations and all 32 seeds. They are the review's "64 hit-free F2 cells" and must be reproduced entirely by the treatment.
- **Population sizes.** The standard exposed population is 4,160 cells (F1 2,880 + F2 576 + F4 704), and the standard stalemate population is 738.
- **Companion.** The K = 1 companion control has no recovery and therefore no stalemate, as K = 1 implies.

## Control baseline (§M rule 6)

Every hypothesis quantity was computed on the control before any treatment exists, and frozen in the same record. These are control facts, not E3 results.

| Quantity | C-E2 (primary) | C-RS (companion) |
|---|---|---|
| Outcome classes, exposed standard cells | A 1,389 · B 1,127 · tick-limit tie 1,536 · mutual elimination 108 | A 1,731 · B 1,297 · tie 1,024 · mutual 108 |
| Stalemate PM-1 (D1 / D4 / D8 population) | 738 cells: 642 scoreable, 96 `NOT_SCOREABLE`; median PD 1.0, median FMS 1.0; 589 first-mover-dominated, 53 first-mover-leaning; n_distinct 103 | empty population |
| Stalemate PM-2 | 1,476 entrant readings: 674 `NO_ZERO_CORE_TICKS`; 802 with a phase-lock, all opponent-first, all \|2·PL − 1\| ≥ 0.9 | — |
| C-E2 seat-determined units (D2) | exactly the six registered: probe v sniper, probe v spread sniper, sniper v spread sniper (F1, Seat A); probe and sniper mirrors (A); guarded-painter mirror (B, n_distinct 29) | the same six, with the guarded-painter mirror favouring A (n_distinct 30) |
| F4 seat-determined units (separate stratum) | jam sniper v counter (B), jam mirror (A); n_distinct 1 each | the same |
| Mirror claims at 1000 vs 1001 | all ten agree | all ten agree |
| Repair-guard capture losses (D3 cell set) | 192, all exposed | 192 |
| Spread win-or-draw vs stacked (D5) | Seat A 480/512 = 0.9375; Seat B 416/512 = 0.8125 | 0.9375; 0.6875 |
| Jam sniper decisive wins (D6), per seat of 32 | repair guard 32 / 32; disrupt guard 0 / 0; min guard 0 / 0; n_distinct 1 each | repair 32 / 32; disrupt 0 / 0; min 32 / 32 |
| Exposed-F1 tick-limit share (D7) | 0.545 (1,570 / 2,880) | 0.333 |
| Completions against repair and disrupt guards (D9 victims), all fields | 350 | 576 |
| F1 residuals, E2 rule (eligible and significant) / §M rule 4 count | Seat A 7 / **0**; Seat B 10 / **0** | 6 / 0; 8 / 0 |
| MC-1 / MC-2, standard fields | exclusive share 0.622; second mover mean 2.50 executed, mean ADF 0.688; first mover 6.80, 0.150 | 0.481; 3.37, 0.579; 6.48, 0.191 |

Every E2-significant control residual that §M rule 4 excludes is either a dominance pairing or below the 1/8 floor. That includes min guard v greedy painter in Seat B (−0.178, n_distinct 8): the painter wins every distinct trajectory there, so it is dominance. The frozen control counting set is therefore empty in both seat tables, and any residual that counts under T-E3 will be new relative to the control.

## Pre-treatment findings (control data only; nothing changed)

These were found on control data before any treatment exposure. Each is reported, and none was acted on. The pre-registration is not edited.

- **P-1. D5's "supported" branch cannot be reached in the Seat-A table.**
  - C-E2's pooled Seat-A win-or-draw rate is already 480/512 = 0.9375, so a rise of ≥ 0.10 would need a rate above 1.
  - The spread sniper alone is at 1.0 in Seat A, so no per-agent reading that includes it can rise either.
  - Under the frozen criterion, D5 can therefore only be REFUTED or NEITHER.
  - This is a ceiling in the review's criterion given the E2 control (the review's own prior for D5 is "Fails"). It is not a tooling defect, and D5 is not used in the interpretation table.
  - There are two ways forward, both decided before any treatment exists:
    - accept it as a registered limitation;
    - re-register D5's operationalization under a new analysis freeze, v2, which would still be blind to treatment.
  - This phase does neither.
- **P-2. D6 can only be supported through the min guard.** This is an analytic consequence, not a defect. Under C-E2 the jam sniper already beats the repair guard decisively in both seats, 32 of 32. Under T-E3, G.5 (and the D9 stop check) forbids any capture of the repair and disrupt guards, so a decisive jam-sniper win against either would be a D9 violation and a hard stop. D6's "supported" branch under T-E3 therefore depends only on the min guard.
- **P-3. The review's F2 corpus figures use hit-bearing cells as the denominator.** This is recorded in §The action/parity analyzer above. The frozen metric definitions are unaffected.
- **P-4. 96 of the 738 control stalemate cells have fewer than 10 swings.** They are `NOT_SCOREABLE` under the control and are counted, not dropped (PM-1). The D1, D4 and D8 medians are over scoreable treatment cells, with the not-scoreable count reported alongside.

## D9 real-fixture gate

**PASS** (`d9_real_fixture_gate.json`, SHA-256 `2711d9637fded384783d71f1a5ac2bcc5294a0cd4acecf96c0495c2e25a5f2b5`).

The implementation phase proved G.5 with scripted guards. This gate checks it on the real, tracked `e2_repair_guard` and `e2_disrupt_guard`:

- **Loading.** Each guard is loaded exactly as a match loads it (`ProcessMatchController.from_python_entrants`), and each artifact is finalized by the engine's own code (canonical replay and `result.json`).
- **Adversaries.** The other seat is a scripted adversary: a tracked host fixture whose executor is replaced. The eleven adversaries are an omniscient jammer that reads the controller, an every-action anchor jammer, an in-tick hit/erase alternator, and eight seeded random jammers. None is a matrix entrant.
- **Settings.** Seeds 42, 1001 and 1002 are all outside the matrix; both guard seats; 1000 ticks.
- **Analysis.** Each replay is read back with capture analyzer v2 and the E3 analyzer.

| | Primary treatment Ruleset (K = 2, λ = 1) | Whole-tick parent (sensitivity) |
|---|---|---|
| Scenarios | 132 (2 guards × 2 seats × 11 adversaries × 3 seeds), every one to tick 1000 | 132 |
| Completions against the guard | **0** | repair guard captured in **60 of 66**; the six not captured are the pure anchor jammer, which only ever erases core cell 0 |
| Maximum zero-core streak | 1 | — |
| Zero-core evaluations | repair guard 0; disrupt guard 3,360, **all on its own first-mover ticks**, never two running | — |
| Minimum executed actions (first / second mover) | **5 / 4**, the G.4 bound, tight | — |
| G.4 violations, zero-action live ticks, analyzer problems | 0, 0, 0 | analyzer problems 0 |

This is an implementation consistency gate. It is not a treatment result, and no matrix cell was exposed.

## Treatment prefix gate (implemented; exercised on control data only)

`gates.prefix_gate` enforces hard stop 6 for the future treatment:

- every treatment replay must equal its control through the control's first disruptive hit (tick records `0 … hit−1`, and the header's static part);
- a hit-free control cell must be reproduced entirely, including the result;
- the control's hit-free cells must be exactly the frozen ones (C-E2: the 64 F2 and 64 F2-P repair-guard mirror cells).

It was exercised as follows:

- **Control against itself:** PASS.
- **Tamper cases:** a change before the first hit fails, a change after it passes, a change anywhere in a hit-free cell fails, and a mismatched frozen hit-free set fails.
- **Real λ = 1 against λ = None replays**, in a non-matrix hit-free scenario (the real repair guard against an idle scripted seat, 300 ticks): PASS, identical entirely.

The treatment's `treatment-gates` command runs it together with integrity, the λ = 1 manipulation checks (zero exclusive ticks, no zero-action live tick, no G.4 violation, Σ `cpu_used` = `cpu_total`, capture agreement) and, for T-E3, the D9 stop. When the whole-tick control corpus is presented as a treatment, those gates **fail**: the exclusive-tick and G.4 checks, and the D9 stop on the control's real guard captures. That failure is the intended behaviour.

## Clean-checkout reproducibility

A `git archive` of `b8ac343` was extracted to a scratch directory. Its root `agents/` runtime catalogue was deleted, so nothing could resolve from it, and every import was forced to resolve from the export (`PYTHONPATH` = export `engine/src` and export root; each module's `__file__` was checked).

| Check | Result |
|---|---|
| `battle_engine`, capture analyzer v2 and every E3 module import from the export; the harness's `REPO_ROOT` is the export | yes |
| No `.git`; no root `agents/` directory | yes; yes |
| E3 jam sniper and twin resolve, from `tools/research/v6/e3/fixtures/agents/` | yes |
| All 22 matrix entrants (the 20 reused E2 fixtures and the 2 E3 fixtures) resolve from tracked sources | 22 / 22 |
| Live fingerprints equal the frozen ones | yes |
| Fresh data root from tracked sources resolves every entrant | yes |
| Matrix loads; digest verifies; id `v6-e3-matrix-v1-634132ec3c15` | yes |
| Pre-registration loads; SHA-256 `2b5f82b4…` | yes |
| Analyzers import | yes |
| Capture analyzer v2 unchanged: version 2, SHA-256 `b818f53e…`; E2 freeze `v6-e2-freeze-v2-db6458596d82` still loads | yes |
| E3 analysis freeze `v6-e3-freeze-v1-506811e78ad8` loads against the exported tooling | yes |
| Matrix count; real-planner dry run | 19,456; 19,456 planned, all consistent |

The E3 fixture, matrix, analyzer and freeze test modules also run from the export: 73 passed and 3 skipped. The three skips are the checks that need `.git` history.

## Mutation testing

Each mutation was applied to the committed tooling (`d1f69b9`), and its detecting tests were run. The file was then restored with `git checkout`, and the tree was verified clean before the next mutation. Nothing was committed.

| # | Mutation | Detected by (failing tests) |
|---|---|---|
| 1 | FMS made one-sided (PD = max(0, 2·FMS − 1)) | `test_parity_dependence_is_two_sided`, `test_parity_criteria_are_two_sided` (5) |
| 2 | `NO_ZERO_CORE_TICKS` read as phase-lock 0 | `test_no_zero_core_ticks_is_a_category…`, `test_whole_tick_stalemate…` (2) |
| 3 | Cells with fewer than 10 swings scored | `test_fms_is_scored_only_from_ten_swing_ticks…`, `test_parity_medians_exclude_but_count_not_scoreable_cells` (2) |
| 4 | Duplicate trajectories counted independently | `test_duplicated_seed_trajectories_are_one_distinct_transition` (1) |
| 5 | Mirror claims accepted without the 1001 check | `test_d2_supported_needs_falls_no_new_unit_and_1000_1001_agreement` (1) |
| 6 | The \|R\| ≥ 1/8 residual floor removed | `test_residual_table_marks_dominance_and_applies_the_floor` (1) |
| 7 | The control-side residual comparison removed | `test_residual_counts_only_above_the_floor_without_a_counting_control` (1) |
| 8 | The `cpu_used` cross-check corrupted | `test_cpu_used_cross_check_detects_a_statistics_mismatch` (1) |
| 9 | A request override allowed | `test_any_request_override_fails_closed` (4) |
| 10 | A fixture fingerprint drifted (jam sniper source edited) | `test_fingerprints_are_frozen…`, `test_fingerprint_drift_fails_closed` (2) |
| 11 | One matrix count altered (seeds 1–31) | `test_matrix_definition_is_frozen`, `test_fields_and_expected_match_counts` (2) |
| 12 | A sample parent gate allowed to authorize treatment | `test_only_a_complete_non_sample_record_permits_treatment` (1) |
| 13 | The D9 primary stop check disabled | `test_d9_stop_check_raises_only_for_the_primary_treatment` (1) |
| 14 | *(extra)* Prefix gate ignores differences before the first hit | `test_prefix_gate_on_the_control_side` (1) |
| 15 | *(extra)* G.4 manipulation check disabled | `test_whole_tick_replay_fails_the_slot_limited_manipulation_checks` (1) |
| 16 | *(extra)* D9 real-fixture scenario ignores guard completions | `test_a_violation_fails_the_scenario` (1) |

All 16 were detected. After every restore the tree was clean and `HEAD` was unchanged.

## Tests

| Module | Covers |
|---|---|
| `test_v6_e3_fixtures.py` | Tracked, fingerprinted, research-only fixtures; twin byte identity; the in-tick alternation and the continuing cursor from canonical replays; G.4-tight jamming of a scripted non-matrix victim under λ = 1; determinism |
| `test_v6_e3_matrix.py` | Counts (19,456); the frozen digest; one-field Ruleset differences; fingerprint drift; override and setting guards; the treatment's separate authorization; the treatment-artifact STOP; D0–D9, the interpretation table, metrics, evidence rules and hard stops verbatim against the preserved review |
| `test_v6_e3_action_parity.py` | Two-sided PD; the 10-swing rule; `NO_ZERO_CORE_TICKS`; exact MC-1, MC-2, PM-1 and PM-2 values on real whole-tick replays; the K = 1 forced line's exposure; a hit-free mirror; the `cpu_used` cross-check |
| `test_v6_e3_analysis.py` | Every D0–D9 branch; O-UNIT n_distinct; the 1000/1001 rule; the §M rule 4 residual rule |
| `test_v6_e3_pipeline.py` | A real C-E2 control sample through telemetry, populations, baseline and evaluation; parent reproduction, the prefix gate and the F2-P prefix on real replays, each with tamper cases; treatment gates stopping a whole-tick corpus presented as a treatment; the frozen analysis over both arms |
| `test_v6_e3_d9_gate.py` | The reduced D9 gate on the real guards; the parent's sensitivity; scenario violations; only the full registered gate unlocks |
| `test_v6_e3_freeze.py` | The separate freeze identity; drift detection; capture analyzer v2 pinning; the unlock chain; the committed freeze and the committed control qualification |

## Treatment readiness

`python -m tools.research.v6.e3.run_e3 unlock` reports `{"unlocked": true}` at `8812ffa`. The command is read-only and executes nothing. Before any treatment can run or be analyzed, the unlock chain requires all of the following:

1. The committed freeze `v6-e3-freeze-v1-506811e78ad8` still holds against the live tooling, and capture analyzer v2 is still byte-identical.
2. Its `control_qualification` is `PASS`, and the parent-reproduction, analyzer-qualification and D9 records match their pinned SHA-256.
3. Those records are complete, non-sample, passing and under this freeze.
4. The qualified control telemetry files are unchanged.
5. `control_populations.json` matches its pinned SHA-256 and recomputes exactly from the control corpus.

Execution then additionally requires `--confirm-matrix-execution --confirm-treatment-execution`, a clean tree and the frozen engine and tooling source, checked before and after the run.

**Order for the separately authorized treatment phase:**

1. `execute T-E3 <field>` for F1, F2, F2-P and F4, then the same for T-E3K1.
2. `treatment-telemetry` for each treatment.
3. `treatment-gates` for each treatment. Any failure is a STOP. A D9 completion under T-E3 is a theorem violation, which is an implementation STOP.
4. `analyze`, which writes the criterion statuses for the primary arm and the companion's readings. Verdicts are then read under the interpretation table.

Before authorizing the treatment, decide P-1 (D5's unreachable support branch).

## Treatment-Ruleset exposure in this phase

**No matrix cell ran under a treatment Ruleset.** No seed in 1–32 ran under either treatment, and no treatment corpus exists.

This phase's own work added only scenarios that are not matrix pairings under `bytefray-rules-6-research-capture-hold-k2-disruption-slot1`:

- the D9 real-fixture gate: the real guards against scripted adversaries, at seeds 42, 1001 and 1002, and its reduced form in the test suite at seed 42;
- one fixture test: the jam sniper against a scripted, idling non-matrix victim, seed 42, two ticks;
- one prefix-gate premise test: the real repair guard against an idle scripted seat, seed 42.

**Pre-existing exposure.** The implementation phase's committed characterization tests, `test_e3_slot_limited_disruption_semantics.py`, run a few matrix *pairings* under both treatment Rulesets at seed 42, which is outside the matrix seeds: sniper v disrupt guard, sniper v repair guard, spread sniper v disrupt guard, and the probe and guarded-painter mirrors. They assert mechanics only. They ran unchanged in this phase's baseline and final repository suites, and nothing from them was analyzed or used here. The design review's §I probe and the implementation reconciliation had already reported those same named scenarios.

**Pre-freeze de-risking check.** A seed-1 sample of C-E2 and C-RS for F1 and F2 was deep-compared with the historical corpora (0 mismatches). It was control-only, it is not a gate record, and it can never unlock anything.

## What this record does not claim

- No E3 gameplay result, and no hypothesis verdict. Neither T-E3 nor T-E3K1 was run.
- No prediction that E3 succeeds. The probe priors are predictions to be falsified.
- No threshold, operationalization or fixture set, tuned or changed after the E3 controls ran. The pre-registration was committed (`ebdfb69`) and frozen (`b8ac343`) before any E3 control cell existed. During development, the E2 corpus was already public, and a handful of its preserved control replays were read only to validate the analyzer. The design review's own corpus facts, reproduced above, were computed after the freeze. The D5 ceiling (P-1) was found after the controls ran, and it was reported rather than acted on.
- No change to gameplay, the qualified E3 Rulesets, the scheduler, disruption scope, the replay schema, capture analyzer v2, E2 or V4.

## Addendum, 2026-09-24: P-1 decision and treatment authorization

*Appended after the record above; the text above is unchanged.*

- **P-1 accepted as a documented pre-registration limitation.** D5's criterion stays exactly as frozen. Its "supported" branch cannot be reached in the Seat-A table, so D5 can only be read as REFUTED or NEITHER. There is no re-freeze.
- **Treatment authorized under freeze v1.** T-E3 and T-E3K1 are authorized to run under the unchanged analysis freeze `v6-e3-freeze-v1-506811e78ad8` and matrix `v6-e3-matrix-v1-634132ec3c15`. The treatment then follows the order in §Treatment readiness: execute, treatment telemetry, treatment gates (any failure is a STOP), and the frozen analysis.
