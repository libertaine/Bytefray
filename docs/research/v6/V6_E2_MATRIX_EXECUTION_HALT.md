# Bytefray V6 E2 — Matrix Execution Halt (Capture-Analyzer Defect)

**Status:** Execution **halted before T-E2**. The two control conditions ran in full, and the full structural-control gate passed. The treatment condition was **not executed**, so **no T-E2 data exists** and this note contains no gameplay result and no hypothesis verdict.
**Branch:** `v6-research` @ `062feeb28d84c8da0af3f41716e3b5468e0b3eed` (frozen baseline)
**Matrix:** `v6-e2-matrix-v1-9048907fdc3b`
**Date:** 2026-09-23
**Authority:** [`V6_E2_EXPERIMENT_FREEZE.md`](V6_E2_EXPERIMENT_FREEZE.md) (frozen apparatus), [`V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md`](V6_E2_CAPTURE_HOLD_DESIGN_REVIEW.md) (§H hypotheses, §I matrix, §K telemetry). Neither document is changed by this note.

## Summary

The frozen capture analyzer (`tools/research/v6/e2/capture_analyzer.py`, HD-5) cannot process a valid canonical replay whose seeded core wraps around the end of the arena. At arena 512, that happens on **seed 23**, where Seat A's core base is 506 (cells 506–511 and 0–1). The analyzer raises on every seed-23 replay, and `analyze_e2`, which calls it on every cell without exception handling, aborts before producing any output. As frozen, the E2 analysis pipeline is therefore unable to analyze the frozen matrix.

The execution authorization pre-specified the response. If frozen code must change, stop the experiment and do not patch and continue under the same matrix identity. A changed implementation needs a new qualification and freeze before treatment data can be interpreted. The defect was found while the controls were running, before any treatment match. T-E2 was deliberately left unexecuted so that the fix and re-freeze can be made **without any treatment data in existence**.

## A. Execution provenance

| Item | Value |
|---|---|
| Branch / HEAD | `v6-research` @ `062feeb28d84c8da0af3f41716e3b5468e0b3eed`, 44 commits ahead of `origin/v6-research`, not pushed |
| Tracked tree | Clean before, between, and after every control execution; checked by `git status --porcelain` around each condition/field |
| Source integrity | SHA-256 manifest of all 182 tracked files under `engine/src` and `tools/research/v6`, byte-identical before and after execution |
| Matrix id / digest | `v6-e2-matrix-v1-9048907fdc3b` / `9048907fdc3b09edf82d5da323bf3659b8b2ff158d50c72043257560497427e0`; recomputed and matched |
| Pre-registration digest | `5b0fafd3ffb1e6f79b5d6170196b642cc7461149691f1c031c24d456a9d3b856`; recomputed and matched |
| Agent fingerprints | All 25 live fingerprints equal `matrix.AGENT_FINGERPRINTS`, and are recorded again in every run's `provenance.json` |
| Dry-run plan | 15,360 planned cells, every condition/field consistent (Ruleset, seeds 1–32, both orientations) |
| Pre-execution tests | The six E2/harness test files, 110 passed |
| Environment | Python 3.13.14, `Windows-11-10.0.26120-SP0`, one worker |
| Artifacts | `runs/research_v6_e2/v6-e2-matrix-v1-9048907fdc3b/` (git-ignored, preserved): `C-V4/` 1.9 GB, `C-RS/` 1.9 GB, `control_gate.json` |
| Gate-sample artifacts | `runs/research_v6_e2_gate_sample/` left in place under its own root, never read by any full-matrix step |

**Pre-registration clarifications.** The three corrections approved for execution, O-TOL (±0.05), O-H2-SIGNIFICANCE (`n_distinct ≥ 8` and a 95% interval from 1,000 distinct-trajectory bootstrap resamples that excludes 0) and O-H2-TRIPLE (the defender does not lose to the attacker), were already recorded in `preregistration.json` exactly as approved. The pre-registration was not edited and its digest is unchanged.

## B. Control execution and gate

Controls ran sequentially, one condition/field at a time, through `run_e2 execute ... --confirm-matrix-execution`, with every fail-closed guard active. That meant the digests, the fingerprints, all four request overrides `None`, and the frozen Ruleset, arena, ticks, seeds and orientations.

| Condition | Ruleset | F1 | F2 | F3 | Total | Wall clock |
|---|---|---|---|---|---|---|
| C-V4 | `bytefray-rules-4` | 2,880 | 640 | 1,600 | 5,120 | 885 s |
| C-RS | `bytefray-rules-6-research-scale` | 2,880 | 640 | 1,600 | 5,120 | 905 s |
| T-E2 | `bytefray-rules-6-research-capture-hold-k2` | — | — | — | **0 (not executed)** | — |

**Corpus integrity (controls).** An independent read-only check found the following for all six condition/field runs:

- the exact expected cell set (pair × seed 1–32 × both orientations), with no duplicates, no missing cells and no extras;
- every cell `completed` with a win, loss or tie outcome and no error code;
- `result.json` and `replay.jsonl` present for every cell, and on-disk match directories exactly equal to the recorded cells, so there was no stray or repeated execution;
- every `result.json` carrying the condition's Ruleset;
- provenance with SHA `062feeb…`, `git_dirty: false`, the frozen matrix id, digest, pre-registration digest and fingerprints, no scheduler override, and `e2_sample: false`.

**`run_e2 gate` — FULL CONTROL GATE PASS.**

| Field | Cells compared | Missing (V4 / RS) | Mismatches | Deep replay |
|---|---|---|---|---|
| F1 | 2,880 / 2,880 | 0 / 0 | 0 | yes |
| F2 | 640 / 640 | 0 / 0 | 0 | yes |
| F3 | 1,600 / 1,600 | 0 / 0 | 0 | yes |

The gate compared placement, seats, outcome, winner, decision tick, scores, territory and entrant terminations cell by cell, then every `result.json` and every full replay stream, ignoring only the Ruleset identity fields. Record: `control_gate.json`, `status: PASS`, `complete: true`, provenance `062feeb…` clean, SHA-256 `99b99a346ce72854c039585d0ec04ab1257e0440a2d8cb2f9125fa6b37d5492b`. The per-field subject-perspective outcome tallies are identical between the two conditions, as the gate requires: F1 1,001 / 1,203 / 676, F2 124 / 124 / 392 and F3 729 / 477 / 394 wins / losses / ties.

The record carries `unlocks_treatment: true`, so the runner would now mechanically allow T-E2. **T-E2 was not run** (see *Decision*).

## The defect

**Where.** `capture_analyzer.analyze_replay` builds each entrant's core from the tick-0 seeding diffs ([`capture_analyzer.py:283-295`](../../../tools/research/v6/e2/capture_analyzer.py)):

```python
for diff in ticks[0].memory_diffs:
    cells = _addresses(diff.address, diff.length, arena)
    ...
    if diff.owner in seat_of:
        cores[diff.owner] = cells          # one diff is assumed to be the whole core
for agent in ticks[0].agents:
    if agent.agent_id not in cores or cores[agent.agent_id][0] != agent.pc:
        raise ValueError(... "seeded core ... does not match its recorded pc")
```

**Mechanism.** A core of 8 cells whose base lies within 7 cells of the arena end wraps around the boundary, and the canonical replay records its seeding as **two** diffs. On seed 23 at arena 512, the tick-0 diffs are `(506, 6, A)`, `(0, 2, A)` and `(160, 8, B)`. The second `A` diff overwrites the first, the assembled core becomes `[0, 1]`, and the pc cross-check (`0 ≠ 506`) raises. The ownership map built in the same loop is correct. Only the core assembly assumes one diff per core.

**Scope, measured on both control corpora.**

| | C-V4 | C-RS |
|---|---|---|
| Replays analyzed by the frozen analyzer | 4,960 | 4,960 |
| Replays that raise | 160 (F1 90, F2 20, F3 50) | 160 (F1 90, F2 20, F3 50) |
| Seeds that raise | 23 only | 23 only |
| Wrapped entrant | Seat A (base 506) in every seed-23 match | same |
| Engine inconsistencies in the other replays | 0 | 0 |
| Unattributed completions / onset–killer mismatches | 0 / 0 | 0 / 0 |

- **It fails closed.** All 320 affected replays raise. None of them would pass the check silently with a truncated core, because in every case the base segment is recorded first. A replay whose low segment came first would pass the check with a 6-cell core and produce wrong telemetry without an error, so a fix must not depend on diff order.
- **The frozen pipeline aborts.** `analyze_e2.load_field_run` on C-V4/F1 raises the same `ValueError`, and `analyze_matrix` loads C-V4/F1 first. No condition, field, transition or hypothesis metric is produced, including the ones that do not use capture telemetry.
- **The runtime is not implicated.** In all 92 ordered cells whose other 31 seeds collapse to a single trajectory (53 F1, 14 F2, 25 F3), seed 23 produces exactly that trajectory. Seed 23 is an ordinary trial, and only the analyzer mishandles its geometry.
- **Why qualification missed it.** The analyzer tests run at seed 42 (cores at 485 and 203), the analysis-pipeline test at seed 1, and the gate-qualification sample at seeds 1 and 17. None of these places a core across the boundary, and no test constructs a wrapped core.
- **T-E2 exposure (expected, not observed).** E2 inherits the research-scale seeded placement unchanged, and the gate shows C-RS placements identical to C-V4's. T-E2's seed-23 cells would therefore be expected to wrap in the same way. This was not observed, because T-E2 was not run.

## Affected and unaffected outputs

| Output | Status |
|---|---|
| Control execution artifacts (cells, `result.json`, replays, provenance) | **Unaffected**; complete and integrity-checked |
| Structural-control gate | **Unaffected**; uses `control_gate.py` only, PASS |
| Capture telemetry (onsets, recoveries, completions, zero-core ticks, streaks, phase-lock, zero-core winners, location counts, attribution audit, inference audit) | **Blocked**. The analyzer raises on seed 23, 3.1% of every condition's cells |
| `analyze_e2` (per-field analysis, transitions, all H0–H3g metrics) | **Blocked**. Aborts on the first seed-23 replay |
| Harness outcome analysis (seat tables, SDI, Bradley–Terry, residuals) | Not itself defective, but only reachable through the aborted pipeline in the frozen workflow |

## Decision

Following the execution authorization's stop rules (§1: frozen code that must change stops the experiment, and §12: an analyzer correctness defect stops interpretation, with no patch under the frozen identity):

- **T-E2 was not executed.** Treatment data should not exist before the analyzer is fixed and re-frozen, so the re-freeze stays blind to treatment outcomes. Running T-E2 first and fixing afterwards would make the new freeze non-blind.
- **The analyzer was not patched**, and no workaround was used: no patched scratch copy, and no exclusion of seed 23. Seeds 1–32 are part of the frozen matrix definition, so dropping a seed would change the experiment.
- **No hypothesis was evaluated.** H0–H3g, the negative-result rule, the probe-prior comparison and the E2 disposition all remain open.
- The in-flight C-RS control execution was allowed to finish, and the full gate was run. Both use only frozen runtime and gate code that the defect does not touch. Their results tell the re-qualification whether this control corpus can be reused.

## What a re-qualification needs (recommendations; nothing here is implemented)

1. **Fix core assembly only.** Derive each entrant's core as `[(pc + i) % arena for i in range(core_size)]`, where `core_size` comes from the seeding diffs' total length for that owner. Cross-check that the union of that owner's tick-0 seeding cells equals this set. This is independent of diff order, and the rest of the state machine is untouched.
2. **Add a by-value regression test on a real wrapped core,** for example seed 23 at arena 512, where Seat A's base is 506. Assert the assembled core, a completion and its attribution against the engine's own events, and cover the reverse diff order to close the silent-truncation path.
3. **Qualify the analyzer on the whole control corpus before T-E2.** The 10,240 control replays are a ready qualification set that contains no treatment data. Every one should analyze with 0 exceptions, 0 engine inconsistencies and 0 attribution mismatches. On the 9,920 non-wrapping replays the frozen analyzer already meets this.
4. **Bump `CAPTURE_ANALYZER_VERSION` and re-freeze.** The matrix id is derived from `matrix.py` alone, so an analyzer-only fix would leave it unchanged. Whether the re-freeze keeps this matrix id and reuses the gated control corpus, or issues a new identity and reruns the controls, is a decision for the re-freeze, not for this note. The controls were produced by the runtime at `062feeb`, before and independent of any analyzer change.

## State at halt

- Corpus: C-V4 5,120, C-RS 5,120, T-E2 0; 10,240 of the 15,360 frozen matches.
- Control gate: FULL CONTROL GATE PASS (5,120 / 5,120 cells, 0 mismatches, deep replay).
- Frozen apparatus at `062feeb`: unchanged, with the source manifest identical before and after.
- Scientific question: **unanswered.** Nothing in this note bears on whether K = 2 creates opponent-dependent interaction.
