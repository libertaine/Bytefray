# Bytefray V6 E8 — Active Spatial Sensing: Analysis Freeze (I8-5)

**Status: FROZEN, stopped before the first real E8 seed, awaiting the research lead's review of I8-5.** Phase I8-5 of the [implementation plan](V6_E8_ACTIVE_SPATIAL_SENSING_IMPLEMENTATION_PLAN.md) built the complete instrument that will run and interpret the E8 matrix, and froze it as **`v6-e8-analysis-v1-52e09e5fb422`**. The instrument covers the runner and its unlock chain, trace capture, the E8-D gates, the D8-1 re-derivation, telemetry, payoffs, the analyzer and interpretation, and the seed tooling.
- **What does not exist:** no E8 seed, seed list, seed commitment or execution identity; no seed reveal; no matrix cell; no treatment outcome of any kind; and no match in which one family member played another. Every match I8-5 played was between scripted, non-family agents, at infrastructure seeds.
- **What remains:** I8-6 (seed generation, exactly once), then Q8 and T8. Each needs separate authorization.

**Branch:** `v6-research`
**Date:** 2026-10-01
**Governing records:**
- [pre-registration](V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md) (**PR8**), revision 5, frozen as `v6-e8-prereg-v4-0166cdc0b37a`;
- [implementation plan](V6_E8_ACTIVE_SPATIAL_SENSING_IMPLEMENTATION_PLAN.md) (**plan**), pinned by that freeze and not edited;
- [family freeze record](V6_E8_FAMILY_FREEZE.md) (I8-4).

---

## 1. Identities

| Identity | Value | Phase |
|---|---|---|
| Pre-registration freeze | `v6-e8-prereg-v4-0166cdc0b37a` (unchanged) | I8-0 |
| Structural matrix | `v6-e8-matrix-v1-e0d322b597da` (unchanged) | I8-4 |
| Family freeze | `v6-e8-family-v1-981fc8b12beb` (unchanged) | I8-4 |
| **Analysis freeze** | **`v6-e8-analysis-v1-52e09e5fb422`**, record `tools/research/v6/e8/analysis_freeze.json`, digest `52e09e5fb422e7f90f912b4ceccf40b137286d2915e5e2a14ec76eb89288b106`, tooling commit `6d3930a` | I8-5 |
| Seed commitment and execution identity | `v6-e8-exec-v1-<12 hex>`: **do not exist**. The record's `seed_commitment` block is PENDING. | I8-6 |
| Control qualification | **PENDING** | Q8 |

**What the analysis identity pins** (inside its digest):
- the three identities above, each of which must still load;
- the analyzer, gate, re-derivation, telemetry, trace and runner versions;
- the SHA-256 of 24 E8 tooling files and 18 reused E2 to E6 files;
- all 23 E8 qualification test files, from I8-0 to I8-5;
- the engine source manifest, which must equal the one the family was qualified on (116 tracked files under `engine/src`, `9323307c…2676`);
- the I8-1 parent freeze;
- the conventions I8-5 fixed (§6).

The seed block and the control block sit outside the digest, as in E6.

## 2. Phases and Commits

| Phase | Commits | Content |
|---|---|---|
| I8-0 to I8-4 | `83ae0c6`, … `3453432` | The registration, parent goldens, engine surface, family, family freeze |
| **I8-5** | `6d3930a`, `8eeaf86`, this commit | The instrument and its 149 tests; the analysis freeze and its 11 tests; this record |

## 3. The Instrument

| Module | Role | Registered items |
|---|---|---|
| `seed_protocol.py` | E6's seed tooling with E8's names: one generation, the canonical encoding, the commitment, `v6-e8-exec-v1`, a write-once private list under `runs/`, D8-10, and `SeedGuard` | §9 steps 2 to 6, D8-10 |
| `traces.py` | Bound traced re-execution of every cell; storage; the callback rows with absent kept distinct from `null`; the replay's byte write log | §10, D8-12 |
| `rederive.py` | D8-1's independent re-derivation of every SENSE's status and tuple, on E6's qualified scheduler simulation | D8-1, D8-4, D8-5 |
| `gates.py` | D8-1 to D8-5, D8-7, D8-8, D8-11 to D8-15, CQ8-1, CQ8-2, and the E8-D aggregator | §5.1, §5.2 |
| `telemetry.py` | O-ACQ, O-REACQ, O-VERIF and the mechanism quantities, from a trace-only reconstruction of KU-1 to KU-9 | §4, §6.3, §6.5 |
| `payoff.py` | PR6's payoffs, best responses and universality, imported from E6 unchanged, with E8's sets; BR^A, Q_none, L8, Δ^R, U | §4, §5.3 |
| `analyze_e8.py` | Every registered quantity per arm, with identical code; CQ8-4; CQ8-5; the interpretation; the companion | §5 to §8 |
| `run_e8.py` | The unlock chain: `plan`, `generate-seeds`, `execute`, `qualify`, `treatment-gates`, `analyze`, `reveal`, `interpret` | §9, §11, §12, §13 |
| `analysis_freeze.py` | `v6-e8-analysis-v1` | §11, rule 7 |

**`decision.py` (I8-0) supplies every registered status, row, qualifier, reading, label, core answer, kill and disposition.** The analyzer supplies only their inputs, and restates no threshold, set or text.

**Reused, unchanged and pinned:**
- E6's payoff functions, scheduler re-derivation, trace capture and descriptive alternation;
- E6's O-CONTACT reading;
- E4's seat metrics and FMA/FPS;
- E3's outcome classes;
- the E6 post-hoc audit's per-seed seat decomposition;
- the experiment harness.

## 4. The Two Hard Preconditions

As the research lead directed at the I8-4 close, both run before anything is written, and a failure in either leaves no match artifact.

**`execute` runs these checks in this order, all before any write:**
1. The analysis freeze loads, which also loads the family and pre-registration freezes.
2. The committed seed list matches its commitment, and the execution identity recomputes.
3. For a treatment, a PASS control qualification with committed strata. For a control, no treatment artifact may exist.
4. The structural matrix verifies, and D8-9 passes.
5. **`family_freeze.verify_engine_source`** holds: the engine is the one the family was qualified on.
6. `verify_execution_source` holds: a clean tree, and every pinned tooling and reused file equals its content at the tooling commit.
7. **`compatibility.require_compatible` passes for every planned match of the field**, on the frozen packages.

**Then, once those checks pass:**
1. The packages are copied into the field.
2. Each copy is checked against the family freeze's fingerprints.
3. Every match is gated again on the copied packages, which are the ones that will load.
4. The field runs.
5. Every cell is re-executed traced, **with `require_compatible` immediately before each traced match**.
6. The engine and tooling are re-verified after the field.

**One precise point.** The first, untraced execution of a field goes through the harness's `EvaluationService`, which has no per-match hook. Its matches are therefore gated before the field starts: every planned match, by its two packages and Ruleset, which fully determine the gate's answer. The gate does not run between those matches. The traced pass then gates each match immediately before it runs. No match of either pass can start with a pairing the gate refuses.

**Evidence** (`test_v6_e8_runner.py`, `test_v6_e8_traces.py`):
- the real planner plans and gates all 16,896 cells;
- an ungated package is refused with the data root unchanged;
- a failing engine check stops before the pre-match gate is reached;
- a tampered package copy is refused;
- a traced re-execution of an ungated package is refused before its run directory exists.

## 5. E8-D, CQ8 and the Analysis

| Clause | Evaluated on | Implementation | Planted failures that fail it |
|---|---|---|---|
| D8-1 | T8, T8L; presence all four | `rederive`; presence of `sensed_anchors` | a changed tuple, a dropped field, a stray field (under C8 and T8), a refusal with a list, an applied `null`, a status the reach contradicts |
| D8-2 | T8, T8L | every visible set empty | a visible leak |
| D8-3 | T8, T8L | 576 matched LURK8/GREED8 stream digests per condition | a divergence, a missing cell, an absent field against a `null` one |
| D8-4 | T8, T8L | ≤ 8 callbacks per entrant and tick, and re-derivation alignment | an extra uncharged offer after a SENSE, 9 callbacks in a tick |
| D8-5 | T8, T8L | replay byte write log equal to the traced applied WRITEs, in order; no position change | a changed write value, a moved anchor after a SENSE |
| D8-7 | C8, C8L | tick-0 distances > 32 | a 32-cell layout, a 17-cell layout across the wrap |
| D8-8 | all four | early core writes only after an information event | a blind write; a SENSE result not yet delivered |
| D8-11 | F2, all four | byte-identical replay tick records and the same winning seat | a changed tick record, a missing orientation |
| D8-12 | all four | trace for every cell, bound to its replay, and a record for every predicted callback | a missing cell, a mis-bound trace, a lost record |
| D8-13 | presence all four; reflection T8, T8L | exactly one delivery per SENSE, equal to its result | a mismatch, a dropped reflection, a stray field (under C8 and T8) |
| D8-14 | all four | `APPLIED` or `REJECTED_OUT_OF_REACH` only | `REJECTED_INVALID`, `EXCEPTION`, an unknown status, a missing status |
| D8-15 | all four | 27 on every T8/T8L reset record; absent from every C8/C8L one | 26, an absent treatment window, a `null` treatment window, a control `null`, a control 27, no reset record |
| CQ8-1 | C8, C8L | no SENSE record, and D8-14 | a control SENSE record |
| CQ8-2 | C8, C8L F1 | RUSH8 = REACQ8 before the first re-acquisition trigger; GUARD8 = EVADE8 before the first inferred hit | a changed trigger, a missing compared cell |
| CQ8-3 | the family freeze | the census, non-empty | — |
| CQ8-4 | both arms | `decision.control_against_control` | a treatment slot that is not the control is refused |
| CQ8-5 | C8 | O-NEUTRAL at the point estimate; committed in the qualification record, which a treatment requires | a qualification record without strata is refused |

**Every clause and check holds on real artifacts.** Scripted agents played under all four conditions through the real evaluation path. Their traces passed every clause, thousands of applied and refused SENSEs were re-derived exactly, and the replay and trace write logs agreed byte for byte.

**The analysis** is qualified on designed synthetic tables whose registered statuses are known in advance (`test_v6_e8_analysis.py`):
- a cyclic table supports H8-SUB, H8-PAR, H8-CHANNEL and H8-LESS, refutes H8-REPEAT, and fires nothing;
- a universal RUSH8 fires KC8-1, a *search race*, and KC8-6, a *channel race*;
- a universal GREED8 fires KC8-1 as *greed dominance*, and KC8-2;
- LURK8 alone universal in A8 fires KC8-6 as *information dominated*;
- REACQ8 beating EVADE8 supports H8-REPEAT, and H8-ADAPT then reads SUPPORTED or REFUTED as designed; it is recorded only when interpretable;
- forced lines support H8-FL and fire KC8-4;
- seat-determined pairings flag 55 units, support H8-SEAT with ΔG = 5/6, and fire KC8-5 in both layers;
- a stalled treatment raises PF8-1 to PF8-3, refutes H8-TAX and fires KC8-3;
- CQ8-4 PASSes with the control in the treatment slot;
- a failed gate gives STOP, NOT EVALUABLE and VOID.

The payoffs equal an independent computation and PR6's functions. The per-seed seat decomposition equals E4's own metrics at the point estimate, and a corrupted unit is refused.

## 6. Settled at I8-5, for Review

Each was fixed before any seed, and each is recorded inside the analysis identity (`conventions`):
1. **Trace capture is E6's bound re-execution.** A trace is accepted only if the replay bytes, `match_id` and `result_id` reproduce the evaluated cell, and the trace's `BindingRecord` names that replay.
2. **P8-11, storage.** Every cell's trace is kept, gzip-compressed, with no retention subset, as D8-12 requires.
   - **The measured estimate, made without any family match:** full-length scripted matches under T8 and C8 (both entrants alive for 1,000 ticks, 8,400 to 12,000 callbacks) stored 147 to 170 KB per cell. Scaled to the 16,000-callback maximum, that is at most about 230 KB per cell, so **at most about 3.8 GB for the matrix**.
   - **E6's own corpus**, the nearest measured family traces (C-E6 F2), averaged 38 KB per cell, about 0.65 GB at E8's size.
   - The runner records the measured projection on the first field it executes.
3. **P8-13, line endings.** Traces are stored with CRLF normalized to LF, and `trace_sha256` is over the LF bytes. The raw form is recorded: CRLF on this machine.
4. **A refused SENSE's `normalized_address`** is not registered (PR8 §10 registers it for an applied SENSE only). The engine writes `null`. The re-derivation checks the address only when the SENSE is applied.
5. **D8-8's information events** count from the row whose observation delivers them: a visible set, a delivered SENSE tuple, or a delivered READ result showing an opponent-owned core cell. For a two-process entrant this is slightly stricter than E6's next-row convention. It is the earliest point at which an agent can know the result.
6. **O-VERIF:**
   - under active, ADAPT8's verification SENSEs;
   - under passive, ADAPT8 has no verification action, so its verification observations are counted, descriptively;
   - V(j) is E4 and E5's exact median over the seeds.
7. **O-REACQ's cause.** *Evasion* if the opponent applied a MOVE between the row at which the missing address was last known and the replacing row; *own movement* if only the member moved; *neither* otherwise. It is computed for the members that re-acquire, and is descriptive only.
8. **H8-SEAT's resampling** uses the post-hoc audit's per-seed functions, because E4's functions cannot take a multiset. They are checked against E4 at the point estimate.

## 7. Findings for the Research Lead

1. **A collision between the plan's module name and frozen tests.** The I8-0 pre-registration-freeze test, the I8-1 parent-goldens test and my own I8-4 family-freeze test all check that no seed exists by asserting that no `seeds*` file is in `tools/research/v6/e8/`. The plan's module table names the seed tooling `seeds.py`, which would fail all three. The I8-1 test is pinned by the family freeze, so changing it would break `v6-e8-family-v1-981fc8b12beb`. **The module is therefore `seed_protocol.py`**, and its docstring says why. The three tests are unchanged and stay literally true after I8-6, because the private list lives under `runs/`, outside the package.
2. **"Verification action" under passive.** You confirmed the abstraction at the I8-4 close. One precision for the record: under passive, re-acquisition has no verification *action*. REACQ8 searches only when a tracked anchor goes missing, and ADAPT8's verification observation is the visible set at a tick's first offer. The READ in the family is E6's core-verification READ, an attack-posture step in both modes. N8-6 and the policy encode exactly this; nothing was changed.

## 8. Qualification Evidence

**The new tests** (I8-5), each on scripted, non-family agents or synthetic tables:

| File | Tests |
|---|---|
| `test_v6_e8_seed_protocol.py` | 21 |
| `test_v6_e8_traces.py` | 24 |
| `test_v6_e8_gates.py` | 47 |
| `test_v6_e8_analysis.py` | 26 |
| `test_v6_e8_runner.py` | 31 |
| `test_v6_e8_analysis_freeze.py` | 11 |
| **Total** | **160** |

**The I8-5 run**, at commit `8eeaf86` (which contains the tooling commit `6d3930a`), under the qualification integrity protocol:
- **The full repository suite** (`python -m pytest`, all three `testpaths`): **6,859 passed, 18 skipped, 3 deselected**, in 18 min 19 s.
  - I8-4 gave 6,699; I8-5 adds the 160 above, and nothing else changed.
- **Every E8 test file, I8-0 to I8-5**, before the tooling commit: 1,400 passed and 3 failed.
  - The 3 failures were the `seeds*` collision of §7, finding 1. After the rename, all three passed, together with the renamed module's tests, in a focused re-run.
- **`mypy`** is clean on `engine/src/battle_engine` (97 files) and `client/src/battle_client` (16 files). **`ruff check .`** passes.
- **Integrity.** Before the suite I recorded HEAD, an empty `git status --short`, and the SHA-256 of 376 files: every E8 tooling and test file, every E2 to E6 tooling file E8 reuses, and the tracked `engine/src`. After it, HEAD was unchanged, the tree was clean, and all 376 digests were identical.
- **No engine file changed in I8-5.** The engine source manifest still equals the family freeze's, and the analysis freeze checks that it does.
- **No `runs/research_v6_e8` directory exists**: no seed list, no matrix cell.

## 9. What Does Not Exist, and What Comes Next

No seed, commitment, execution identity, reveal, matrix cell or outcome. The private seed path does not exist.

**Next is the research lead's review of I8-5.** I8-6 needs separate authorization. Following PR8 §9, step 8, the I8-5 boundary should be pushed before it. I8-6 then runs `python -m tools.research.v6.e8.run_e8 generate-seeds --confirm-seed-generation` exactly once, on a clean tree with the freeze loading and its seed block PENDING. The commitment and execution identity, and nothing else, go into the freeze record and are committed and pushed before any control cell. The list itself is never printed, committed or revealed before D8-10.
