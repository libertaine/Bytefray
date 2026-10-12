# Bytefray V6 E2 — Analysis Freeze v2 (Repaired Capture Analyzer, Control-Data Requalification)

**Status:** The capture analyzer is repaired, requalified on the preserved control corpus, and the analysis is re-frozen as **`v6-e2-freeze-v2-db6458596d82`**. **T-E2 has not been executed** and awaits authorization. No treatment data exists, and nothing here is a gameplay result.
**Branch:** `v6-research`. Tooling qualified at `d584ea986be36c748d01c2fbbce36f68cb11a227`; controls generated at `062feeb28d84c8da0af3f41716e3b5468e0b3eed`.
**Date:** 2026-09-23
**Predecessors:** [`V6_E2_EXPERIMENT_FREEZE.md`](V6_E2_EXPERIMENT_FREEZE.md) (freeze v1), [`V6_E2_MATRIX_EXECUTION_HALT.md`](V6_E2_MATRIX_EXECUTION_HALT.md) (the halt, commit `cd4737e`). Both are unchanged historical records; the freeze-v1 note carries only an appended successor pointer.

## Two identities

The halt showed that one identity was being asked to describe two different things. From this freeze on they are kept apart:

| Identity | Describes | Changes when | E2 value |
|---|---|---|---|
| **Matrix identity** (`matrix.py`) | Which matches run: conditions, agents and fingerprints, seeds, pairings, arena, tick limit | The experimental design changes | `v6-e2-matrix-v1-9048907fdc3b` (unchanged) |
| **Freeze / analysis identity** (`analysis_freeze.py`) | The complete instrument that interprets them | Any analysis tooling changes | `v6-e2-freeze-v2-db6458596d82` |

The matrix was not renamed, because its design did not change: the same three conditions, the same 25 agents and fingerprints, seeds 1–32, the same pairings, arena 512, 1000 ticks. Only the post-processing of wrapped core geometry was wrong.

## Freeze v2 identity

`freeze_id = v6-e2-freeze-v2-` + the first 12 hex digits of the SHA-256 of the canonical identity:

| Input | Value |
|---|---|
| Matrix id / digest | `v6-e2-matrix-v1-9048907fdc3b` / `9048907fdc3b09edf82d5da323bf3659b8b2ff158d50c72043257560497427e0` |
| Pre-registration digest | `5b0fafd3ffb1e6f79b5d6170196b642cc7461149691f1c031c24d456a9d3b856` (unchanged) |
| Capture analyzer version / digest | 2 / `b818f53e32ba160fb55386cddccd555812def9dc7c54434923c7451fa2c18f86` |
| Analysis tooling | SHA-256 of all ten instrument files: `experiment_harness.py`, and under `e2/`: `analysis_freeze.py`, `analyze_e2.py`, `capture_analyzer.py`, `control_gate.py`, `matrix.py`, `preregistration.json`, `preregistration.py`, `requalification.py`, `run_e2.py` |
| Tooling source commit | `d584ea986be36c748d01c2fbbce36f68cb11a227` |
| Control source commit | `062feeb28d84c8da0af3f41716e3b5468e0b3eed` |
| Match-generation source | `engine/src` tree `5b7495eea683637e5cdddc4be7f08da7e2ba5ec1` (at `062feeb`) |
| Freeze digest | `db6458596d82127e7b563cef0be9318c83f50e47de8d1990b0d9fe9b9a5a3fc4` |

The committed record is `tools/research/v6/e2/analysis_freeze.json`. `load_freeze` fails closed unless its digest recomputes and every live input still equals the record. Changing any tooling file, the analyzer version, the matrix or the pre-registration therefore invalidates the freeze. A test pins the committed record against the live tooling.

## The repair (capture analyzer version 2)

Version 1 assembled each core from a single tick-0 seeding diff, so a core within seven cells of the arena end (seeded as two diffs) was overwritten by its second diff and failed the pc cross-check. Version 2 rebuilds the core as the contiguous run of the entrant's seeded cells starting at its recorded `pc`, modulo the arena. It fails closed unless the union of those seeding cells is exactly that run, whatever their order. A non-integer `pc` also fails closed. Nothing else in the capture state machine changed.

New tests (`test_v6_e2_capture_analyzer.py`). Each **fails on version 1** and passes on version 2, which was checked by running them against the version-1 file:

| Test | What it pins |
|---|---|
| Real seed 23, E2 and V4 | Seat A's core at 506 is seeded as `(506, 6)` + `(0, 2)`, and under E2 B's tick-2 attack on it is also recorded across the arena end. The analyzer reports core 506 / size 8. A reaches zero core at tick 2 only because cells 0 and 1 count, B completes at tick 2, A wins at zero core, and every count agrees with the engine. Under V4, A owns all 8 cells. |
| Synthetic core at 509 (independent of seed 23) | The attacker takes seven cells on tick 1 and spares cell 4, past the arena end. The victim therefore has **no** onset on tick 1 (a core cut at the arena end would have shown one), then onset at tick 2 and capture at tick 3, credited to the attacker. |
| Seeding-diff order | The same replay with its tick-0 diffs reversed yields identical telemetry. This closes the silent-truncation path the halt record flagged. |
| Not a run from its `pc` | A seeded core that is not the contiguous run from its recorded `pc` raises. |

## Freeze apparatus

- **`analysis_freeze.py`** computes the identity, builds and verifies freeze records, and before any T-E2 match checks the execution source: a clean tree, `HEAD:engine/src` equal to the controls' tree, and every tooling file equal to its content at the tooling commit.
- **`requalification.py`**, on control data only, checks:
  - corpus integrity: the exact frozen cell set, completed cells, artifacts, no stray match directories, and provenance from `062feeb` with a clean tree, the frozen digests and the fingerprints;
  - the analyzer on every control replay: 0 failures, 0 engine disagreements, 0 attribution mismatches;
  - cell-by-cell C-V4/C-RS telemetry equivalence.
- **`run_e2 requalify`** runs that and re-runs the full control gate. It writes both records under `runs/research_v6_e2/<matrix id>/freezes/<freeze id>/`, so the freeze-v1 gate record at the matrix root is never overwritten.
- **T-E2 unlock chain** (`run_e2.treatment_unlock`, used by `execute` and `analyze_e2`): the committed freeze holds; then a complete passing gate recorded under that freeze; then a complete passing requalification recorded under that freeze; then (execution only) the execution-source check. T-E2 provenance records the freeze id.

## Requalification gate (steps 1–8)

| # | Requirement | Evidence |
|---|---|---|
| 1 | Wrapped-core reconstruction from the recorded start modulo the arena | Capture analyzer v2, commit `12c2121` |
| 2 | Real seed-23 test (base 506 → cells 506..511, 0, 1) | `test_seed_23_core_wrapping_the_arena_end_is_rebuilt_from_its_start` |
| 3 | A synthetic wrap case independent of seed 23 | `test_synthetic_wrapped_core_counts_its_cells_past_the_arena_end` (core at 509), plus the order and fail-closed tests |
| 4 | Analyzer version and digest bumped | `CAPTURE_ANALYZER_VERSION = 2`, digest `b818f53e…` in the freeze identity |
| 5 | Analyzer over all 10,240 preserved control replays | 10,240 analyzed (C-V4 and C-RS × F1 2,880, F2 640, F3 1,600), including the 320 seed-23 replays that version 1 could not process |
| 6 | 0 failures, 0 engine disagreements, 0 attribution mismatches | 0 / 0 / 0; all six integrity checks PASS; C-V4 vs C-RS telemetry differences **0** of 5,120 pairs |
| 7 | Full C-V4/C-RS control equivalence re-run with the repaired analyzer | Gate PASS, complete: 5,120 / 5,120 cells, 0 mismatches, 0 missing, deep replay comparison |
| 8 | New analysis identity frozen | `analysis_freeze.json`, `v6-e2-freeze-v2-db6458596d82` |

Requalification ran at `d584ea9` with a clean tree (Python 3.13.14, `Windows-11-10.0.26120-SP0`, 16 analysis worker processes), and the source manifest was byte-identical before and after. Completions derived per field and condition were F1 1,956, F2 392 and F3 1,078. Version 1 had reached 1,894, 378 and 1,044 on the replays it could process, and the difference is exactly the seed-23 cells.

| Record | SHA-256 |
|---|---|
| `freezes/v6-e2-freeze-v2-db6458596d82/control_gate.json` | `01949677a2769b8940ce3262901d5ee35e304a094cd9029c2a9494d235d40bd2` |
| `freezes/v6-e2-freeze-v2-db6458596d82/analyzer_requalification.json` | `25fbc1f9c4def5f894f33ba24a4e1045d0c01af6c2cf6de2071aee1a88623f47` |
| Freeze-v1 `control_gate.json` (matrix root, untouched) | `99b99a346ce72854c039585d0ec04ab1257e0440a2d8cb2f9125fa6b37d5492b` |

## Why the controls were reused

The 10,240 control matches were generated from the frozen `062feeb` source. They are complete, provenance-clean, and passed the full equivalence gate, and the defect lay entirely in post-processing. Rerunning identical matches would add cost without adding validity. The freeze pins the controls' engine source tree, so T-E2 can only be generated by the same engine. The controls would have to be rerun only if a fix touched match-generation code or the preserved artifacts failed an integrity check. Neither happened: `engine/src` is unchanged since `062feeb`, and all six integrity checks pass.

The analyzer was repaired and requalified using control data only. At no point in this phase did any T-E2 match exist.

## Verification

- Test suite at `d584ea9`: the full repository suite (`_legacy/tests`, `engine/tests`, `client/tests`; GUI tests deselected as `pytest.ini` configures) **3,406 passed, 18 skipped, 3 deselected** in 276 s. The ten E2-related test files (the six apparatus files, the new freeze file, and the E2 Ruleset, semantics and K=1 byte-identity files): 203 passed, including 13 new tests (4 analyzer, 9 freeze and requalification). This commit adds a fourteenth, which pins the committed freeze record against the live tooling.
- `ruff check .`: all checks passed. `mypy --explicit-package-bases` on the six changed or added tooling modules: no issues. `engine/src` and `client/src` are unchanged.

## State

- Matrix `v6-e2-matrix-v1-9048907fdc3b`: C-V4 5,120, C-RS 5,120, T-E2 **0**.
- Analysis freeze `v6-e2-freeze-v2-db6458596d82`: requalified on control data and frozen.
- **T-E2 is not authorized by this note.** Once authorized, it runs as `run_e2 execute T-E2 F1|F2|F3 --confirm-matrix-execution` (5,120 matches), under every guard above.
