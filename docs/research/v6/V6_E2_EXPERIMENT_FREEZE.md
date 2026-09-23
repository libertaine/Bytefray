# Bytefray V6 E2 — Harness Remediation and Frozen Experiment Definition

**Status:** Research apparatus implemented and frozen. **The E2 experiment matrix has not been run**, and nothing in this note is a gameplay result.
**Branch:** `v6-research` (baseline `33e91822153a4ea0fc5ada786a82d87310607baa`)
**Authority:** [`V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md`](V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md) (§G agents, §H hypotheses, §I matrix, §K telemetry). This note records how that design was implemented; it does not restate or change the review's findings. The Ruleset itself is recorded in [`V6_E2_CAPTURE_HOLD_REGISTRATION.md`](V6_E2_CAPTURE_HOLD_REGISTRATION.md) and is unchanged by this phase.

## Scope

This phase prepares the research system so the E2 matrix can be measured correctly:

- it repairs the harness defects HD-1 to HD-7 (review §I.4);
- it adds the §G research fixtures and their mirror twins;
- it adds replay-derived capture telemetry (§K);
- it freezes the experiment definition and the hypotheses.

It changes no gameplay. No runtime, replay, result or product file was touched: capture telemetry is derived from existing canonical replays, and the E2 policy, K=1 byte identity, onset attribution and two-phase capture are exactly as registered.

## Where things live

| Path | Contents |
|---|---|
| `tools/research/v6/experiment_harness.py` | Consolidated harness: runner, provenance, seat-conditioned analysis, rating model (HD-1 to HD-4, HD-6, HD-7) |
| `tools/research/v6/e2/fixtures/agents/` | The ten §G fixtures and their ten twins, with a fingerprint table in its `README.md` |
| `tools/research/v6/e2/capture_analyzer.py` | Replay-derived capture telemetry (HD-5) |
| `tools/research/v6/e2/matrix.py` | The frozen experiment definition and its digest |
| `tools/research/v6/e2/preregistration.json` / `preregistration.py` | Frozen hypotheses, criteria, rules and operationalizations, with a pinned digest |
| `tools/research/v6/e2/run_e2.py` | Thin runner: dry-run plan (default), guarded execution, control gate |
| `tools/research/v6/e2/control_gate.py` | C-V4 / C-RS structural-control equivalence gate |
| `tools/research/v6/e2/analyze_e2.py` | Per-field analysis, transitions, hypothesis metrics; refuses T-E2 without a passing gate |

## Harness repairs

| ID | Defect (review §I.4) | Repair | Regression tests |
|---|---|---|---|
| HD-1 | Pooled metrics were blind to seat determination: a field where Seat A won every match read as 1500 ratings, RMSR 0, no cycles. | Seat-conditioned results come first. Each pairing reports Seat-A wins, Seat-B wins, ties, per-entrant `P(win \| Seat A)` and `P(win \| Seat B)` (with decisive-only rates), the pre-registered SDI and its favoured seat, and seat bias. A `seat_pathology` headline summarizes the field. The rating model is fitted separately to the Seat-A and Seat-B tables. The pooled table is kept, is marked `subordinate`, and warns whenever any pairing is seat-determined. | `test_v6_e2_harness_analysis.py::test_hd1_*` |
| HD-2 | Seeds were treated as independent evidence. | An outcome-level trajectory key (see below) deduplicates runs. Every output carries `n_runs`, `n_seeds` and `n_distinct`, with an evidence label: `deterministic_characterization` (1), `limited_distinct_trajectories` (2–7) or `rate_claim_eligible` (≥ 8, review §I.5 rule 2). The rating model and every bootstrap use the distinct trajectory as the unit, so duplicated seeds cannot change a confidence estimate. Deterministic data reports its standard error as not estimable, never as zero. | `test_hd2_*` |
| HD-3 | Bradley-Terry ran a fixed 50 iterations. | The win graph is split into strongly connected components. Inside each component the MLE exists and is fitted by MM iterations to a tolerance of 1e-10, capped at 100,000 iterations, with the iteration count and convergence reported. Across components the data is separable, the MLE puts the components infinitely apart, and the fit publishes their order instead of ratings. `authoritative` is true only for a converged single-component fit. No pseudo-count regularization is needed, because every finite rating is a within-component MLE. | `test_hd3_*` |
| HD-4 | No mirror cells. | Explicit pairs in the harness, and a byte-identical `*_twin` for every §G agent. Mirrors are reported by `analyze_mirror_condition`, which has no rating table. | `test_v6_e2_fixtures.py::test_hd4_*`, `test_hd4_mirror_*` |
| HD-5 | No capture telemetry. | `capture_analyzer.py` (below). | `test_v6_e2_capture_analyzer.py` |
| HD-6 | The decision-tick median pooled tick-limit matches. | Decision ticks are split three ways: decisive (a winner before the limit; median, quartiles and IQR), mutual elimination, and tick-limit (count, fraction, lengths, score outcomes). | `test_hd6_*` |
| HD-7 | The E2 fixture directory was not a tracked source. | Added to `TRACKED_BENCHMARK_SOURCE_DIRS`. Every matrix agent resolves from tracked files and its fingerprint is frozen. | `test_v6_e2_fixtures.py::test_hd7_*` |

### Statistical model

- **Two layers.** Counts and rates in the descriptive layer are match-weighted over the registered seeds: they describe how often an outcome happened. The model layer (Bradley-Terry, residuals, upsets, cycles and bootstraps) counts each distinct trajectory once. A trajectory repeated across 31 of 32 seeds is therefore a frequent outcome in the descriptive layer, but only one observation of behaviour in the model layer.
- **Trajectory key.** The review's fields (winner, ticks, termination reason, final scores), in seat terms together with who held each seat, plus final territory, the per-entrant termination reasons and the non-outcome status. Seeds, start addresses, ids and hashes are excluded, so a placement-invariant deterministic pairing collapses to one trajectory, and metadata can never split equivalent runs. Merging can only under-count behaviour, so `n_distinct` is conservative.
- **SDI.** Per seed, 1 if the Seat-A entrant wins in both orientations or the Seat-B entrant wins in both. The pairing's SDI is the mean over its distinct seed-level trajectories, that is, over distinct pairs of the two orientations' keys (review §H). A seed-weighted value is reported alongside and labelled descriptive. `seat_determined` means SDI ≥ 0.9 (the H3c threshold).
- **Mirror seat bias.** The Seat-A win rate minus the Seat-B win rate in a mirror.
- **Residuals.** `R_ij` is the distinct-trajectory win rate minus the fitted expectation; across components the expectation is the limiting 1 or 0. A perfectly transitive field has RMSR 0 whether or not it is separable. Per-residual 95% intervals come from 1,000 stratified bootstrap resamples of distinct trajectories. Only pairings with at least 8 distinct trajectories can count as significant.
- **Cycles.** Directed 3-cycles of strict majorities, each listed with its edge rates, margins and `n_distinct`. A cycle is fragile when any edge lies within ±0.05 of 0.5. The Phase 9 count, where every edge is above 0.55, is kept as `robust_cycle_count`.

## Capture analyzer

The analyzer reads one canonical schema-4 replay and rebuilds the engine's capture state machine (review §C.2):

- **Ownership:** the tick-0 seeding diffs, then each tick's memory diffs in execution order.
- **Core:** each entrant's seeding diff, cross-checked against its recorded `pc`.
- **K:** the header's `ruleset_id`, resolved through the Ruleset registry.
- **First mover:** the chunked scheduler with start rotation, so Seat A moves first on odd ticks and Seat B on even ticks.

An entrant is evaluated at tick `t` if it was alive at the end of `t−1` and did not forfeit during `t`.

- **Onset:** a zero-core evaluation that begins a streak.
- **Recovery:** a positive evaluation directly after a zero streak.
- **Completion:** the evaluation at which the streak reaches K.

Onsets are never inferred from kill events.

Per entrant, the analyzer reports:

- onsets, recoveries and completions, with their ticks;
- the zero-core ticks, the maximum streak and the first onset;
- the parity of zero-core ticks and onsets (own-first or opponent-first) and the **phase-lock**, which is the opponent-first share;
- the recovery rate;
- the final ownership, and whether the entrant is capture-threatened at the end;
- the maximum number of distinct process locations;
- the number of writes to the enemy core;
- for the inferring fixtures, an audit of the inferred enemy core base.

Per match, it reports whether the winner ended at zero core and whether every completion is attributed.

**Self-validation.** Every derived completion is cross-checked against the engine's own `core_captured` termination and `kill`/`death` event. The onset capturer is re-derived independently, as the writer that removed the entrant's last owned core cell during the onset tick, and compared with the kill event's `killer`. Any disagreement appears in `mismatches`.

**Inference audit.** The inferring fixtures adopt the enemy core base at their first callback in which every visible enemy anchor is at one address. The replay stores anchors only at tick boundaries. When the enemy moved within a tick, the analyzer therefore reports `ambiguous`, together with every base the agent could have adopted. In the other cases it reports exactly `inferred` or `not_inferred`. It also reports whether every possible base is the enemy's true core. Tests compare the audit with each fixture's actual internal state, recorded by a test-only wrapper, in real matches.

## Frozen experiment definition

`matrix.py`, digest `9048907fdc3b09edf82d5da323bf3659b8b2ff158d50c72043257560497427e0`, matrix id `v6-e2-matrix-v1-9048907fdc3b`.

| Condition | Ruleset | Arena | Role |
|---|---|---|---|
| C-V4 | `bytefray-rules-4` | 512 | Historical control |
| C-RS | `bytefray-rules-6-research-scale` | 512 | Structural parent / control |
| T-E2 | `bytefray-rules-6-research-capture-hold-k2` | 512 | Treatment |

| Field | Composition | Pairs | Matches per condition |
|---|---|---|---|
| F1 (primary) | Triangular round robin of the ten §G agents, in §G.2 table order | 45 | 2,880 |
| F2 (mirrors) | Each §G agent against its twin | 10 | 640 |
| F3 (secondary reference) | {`v4_probe`, `e2_sniper`, `e2_disrupt_guard`, `e2_spread_defender`, `e2_guarded_painter`} × {`Octave`, `nemesis_alpha2`, `v5_core_defender`, `v4_claimer`, `v5_scout_striker`}, cross pairs only | 25 | 1,600 |

The matrix runs seeds 1–32 (given explicitly, not the eight-seed harness default), both orientations, and 1000 ticks. That is 5,120 matches per condition and 15,360 overall. There is no K=3 arm. F2 and F3 are never pooled into the F1 rating tables. The definition also freezes the fingerprints of all 25 agents it runs.

**Guards on every execution** (`run_e2.execute`):

- the matrix and pre-registration digests must match their pinned values;
- the live agent fingerprints must match the frozen ones;
- on the exact `EvaluationRequest`s about to run, `scheduler_chunk_size`, `scheduler_rotate_start`, `kill_weight` and `instr_per_tick` must all be `None`, and the Ruleset, arena, ticks, seeds and orientations must equal the frozen values;
- after the run, the cell count must equal the expected count.

Execution needs an explicit `--confirm-matrix-execution`. `plan`, the default, is a dry run that counts cells with the real evaluation planner and executes nothing.

**Structural-control gate.** `run_e2 gate` compares C-V4 and C-RS cell by cell:

- placement, seats, outcome, winner, decision tick, scores, territory and termination reasons;
- then each `result.json`;
- then the full replay.

Only the identity fields that a different Ruleset id must change are ignored. T-E2 refuses to start, and `analyze_e2` refuses to analyze T-E2, unless a gate record exists for this matrix id that is not a sample, passed, and compared every expected cell of all three fields (review §I.5 rule 3). The `--sample` mode runs every pairing on seeds 1 and 17 only. It exists to qualify the gate mechanism, can never unlock T-E2, and T-E2 has no sample mode.

**Provenance.** Each run's `provenance.json` records the full Git SHA and dirty flag, the Python and platform, the timestamp, the experiment id, the harness id and version, the analyzer version, the Ruleset, the arena, the seeds, the pairs, the agent fingerprints, the matrix id and digest, the pre-registration digest, and the condition and field.

## Hypothesis freeze

`preregistration.json` (digest pinned in `preregistration.py`) holds the following, and loading fails closed if any byte changes:

- the §H statements, supporting and refuting evidence, and probe priors, verbatim;
- the §I.5 interpretation rules and the negative-result rule;
- the thresholds.

Tests compare it line by line with the review's table.

Some criteria cannot be measured as written. Each was given the smallest correction, fixed before any T-E2 data exists:

- **O-TOL.** "≈ 0", "unchanged" and "near 0.5" have no number in the review. They use the only tolerance the review registers, the ±0.05 fragile-edge margin.
- **O-H2-SIGNIFICANCE.** "Significantly nonzero, tested against distinct-trajectory counts" has no procedure in the review. A residual counts only if it has n_distinct ≥ 8 and its 95% interval from 1,000 distinct-trajectory bootstrap resamples (seed 42) excludes 0.
- **O-H2-TRIPLE.** The H2 triple adds the statement's own "defense prevents death" clause: the defender does not lose to the attacker. This is flagged in the file, because without it any transitive ladder would qualify.

The other operationalizations pin one reading of wording that is measurable as written. Examples are what counts as "the sniper" and as "defenders", the H0 cell-by-cell keep criterion, the H3a literal per-match recovery density, and the H3b stalemate population. `analyze_e2.hypothesis_metrics` computes every named metric. It declares no verdicts: those are read under §I.5.

## Operational notes for the matrix phase

- **Measured cost:** about 0.25 s and 0.6 MB of artifacts per 1000-tick match on this machine. The full matrix is therefore roughly an hour of single-worker execution and about 9 GB of artifacts. Replays must be kept, because the capture telemetry is derived from them.
- **Order:**
  1. C-V4 and C-RS for F1, F2 and F3.
  2. `gate`.
  3. Only on a full PASS, T-E2 for F1, F2 and F3.
  4. `analyze_e2`.

  A gate FAIL halts the experiment.

---

## Successor note (2026-09-23): analysis freeze v2

*Appended after the matrix halted. Everything above is unchanged and remains the record of freeze v1.*

Freeze v1's capture analyzer (version 1) could not process a replay whose seeded core wraps the arena end, so the matrix halted before T-E2 ([execution halt](V6_E2_MATRIX_EXECUTION_HALT.md)). The experiment definition above is unchanged: matrix id `v6-e2-matrix-v1-9048907fdc3b`, its digest, the pre-registration and its digest. The analysis instrument was repaired (capture analyzer version 2), requalified on the preserved C-V4/C-RS corpus, and re-frozen as `v6-e2-freeze-v2-db6458596d82` ([analysis freeze v2](V6_E2_ANALYSIS_FREEZE_V2.md)). Two parts of this note describe freeze v1 only. The capture analyzer's **Core** bullet describes version 1, whereas version 2 rebuilds each core from its recorded `pc` modulo the arena. The gate record location and the T-E2 unlock rule under **Structural-control gate** are superseded by freeze v2's freeze-scoped gate and requalification records.
