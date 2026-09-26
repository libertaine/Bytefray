# Bytefray V6 E6 — Priced Sensing: Implementation Record (Checkpoint A)

**Status: RE-FROZEN AS v2 AFTER AMENDMENT 1, AWAITING THE CHECKPOINT A REVIEW OF v2.** This records what phases I-0 to I-6 of the [implementation plan](V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md) built, the first Checkpoint A review, and [amendment 1](V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md). That amendment corrected three defects in the family's implementation before any seed existed, and produced the v2 re-freeze. It covers:
- where the implementation had to settle something the plan did not;
- what the research lead reviewed;
- the evidence behind each phase.

- **What exists:** no seed has been generated, no matrix cell has run, and no family member has played under a treatment Ruleset. The first v1 freeze (`bd3a3ff`) was superseded before exposure. §5 keeps its history, which is not rewritten.
- **What remains:** the research lead's review of the v2 family and freeze. Seed generation (I-7), the controls (Q) and the treatment (T) each still need separate authorization.

**Branch:** `v6-research`
**Date:** 2026-09-25
**Governing records:**
- [pre-registration](V6_E6_PRICED_SENSING_PREREGISTRATION.md) (**PR**);
- [implementation plan](V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md) (**plan**);
- [design review](V6_PRICED_SENSING_DESIGN_REVIEW.md) (**DR**);
- [amendment 1](V6_E6_AMENDMENT_1_FAMILY_CORRECTIONS.md) (**A1**).

---

## 1. Identities

| Identity | Operative (v2) | Superseded before exposure (v1) |
|---|---|---|
| Structural matrix | **`v6-e6-matrix-v2-7de29a4a6954`**. Structural digest `7de29a4a6954216ea215bf8cda3aa792fb62d69ea084bbe2bfd4b42fad6fbfc2`. No seed values. | `v6-e6-matrix-v1-cd040eac42ef`. It differs from v2 only in the matrix version and the package fingerprints. |
| Family policy (`agent.py`, byte-identical in all 18 packages) | SHA-256 `5374092e8c419a01071782cf5383ea481f8d62097acab8adb7064dad20ff3b63` | The I-3 source, as committed at `bd3a3ff` |
| Analysis freeze | **`v6-e6-freeze-v2-275057e27725`**, tooling qualified at `539e26b`. The record is `tools/research/v6/e6/analysis_freeze_v2.json`, committed at `24440b8`. | `v6-e6-freeze-v1-428033032ce2`, tooling at `5f93381`. Its record stays byte for byte at `tools/research/v6/e6/analysis_freeze.json` (SHA-256 `804c57cf…`). It never received seeds or data, and the v2 loader refuses it. |
| Pre-registration transcription | Unchanged: `tools/research/v6/e6/preregistration.json`, SHA-256 `e1ccc1cc7ef2f3b193019590984b9f34fafb0b7e176b1f4ebb8387d0566ee5f4` | The same file |
| Seed commitment and execution identity | **PENDING.** These slots in the v2 record are filled only at I-7, before the first matrix cell. The execution identity keeps its registered scheme, `v6-e6-exec-v1-<12 hex>`, and will bind the v2 structural digest. | Never filled |
| Control qualification | **PENDING.** Filled after Q. The treatment unlock requires it. | Never filled |

Freeze v2's identity names v1 (id, record SHA-256, structural matrix and the amendment). It also states what a trace re-execution is (§3.1).

## 2. Phases and Commits

| Phase | Commit(s) | Content |
|---|---|---|
| I-0 | `ddf0eda` | Parent byte-identity freeze of `research-scale` and `disruption-slot1`: 84 matches, 86 tests. Committed before any engine change. |
| I-1 | `e0625a1`, `5ea1152` | `RulesetPolicy.detection_radius` and `resolve_sensing_radius`; the one visibility line; match-level validation; the two Ruleset identities and their registration. 128 dedicated tests; 10 of 10 mutants killed. |
| I-2 | `aa19daf` | `MatchContextV2.detection_radius` under the direct and the worker executors and in validation; `docs/AGENT_API_V2.md`. 39 tests; 7 of 7 mutants killed. |
| I-3 | `0b34c0c` | 18 family packages, the member table, opaque IDs, fingerprints and the D-5 gate. 135 tests; 20 of 20 behavior mutants killed. |
| I-4 | `c03ea70` | Bound trace capture, compression, retention and the compact-telemetry extractor. 26 tests; 11 of 12 mutants killed. The survivor is equivalent (§3.7). |
| I-5 | `596857a` | Payoffs, bootstrap, hypotheses, flags, kill criteria, interpretation, D-1 re-derivation, the gates, the descriptive sections and the seed tooling. 93 tests; 25 of 25 mutants killed. |
| I-6 (v1) | `5f93381`, `bd3a3ff` | Structural matrix v1, pre-registration transcription, analysis freeze v1, runner, the first version of this record, ROADMAP and FUTURE_PLANS. 44 tests. |
| A1 | `f6418b7`, `539e26b`, `24440b8`, this commit | Amendment 1; the corrected family, the regenerated fingerprints, structural matrix v2 and freeze module v2; the freeze v2 record; this record, ROADMAP and FUTURE_PLANS. Family tests 135 → 326; matrix 19 → 20; freeze 11 → 13. Behavior mutation: 35 of 36 killed. The survivor is equivalent (§4.4). |

**End of amendment 1, at `24440b8`:**
- the full suite gave 5403 passed, 18 skipped, 3 deselected (5209 at v1; the 194 added are the new family, matrix and freeze tests);
- `mypy` is clean on engine (97 files) and client (16 files), and `ruff check .` passes;
- all E6 test files together: 745 tests (551 at v1);
- HEAD, the clean tree and the SHA-256 of every E6 tooling, fixture and test file were identical before and after the suite.

## 3. Where the Implementation Settles What the Plan Did Not

Each item below was fixed before any E6 data existed. **Items 3.1 and 3.2 change how a plan step is carried out.** The rest settle details the plan left open.

### 3.1 Trace capture is a bound re-execution (plan §6.1, corrected; approved at Checkpoint A)

Plan §6.1 says the runner sets `MatchRequest.trace_path` for each cell. It cannot through the evaluation path:
- `EvaluationService` runs each cell through `execute_cell`, which calls `agent_test.test_agent(trace=False)`;
- `tracing: "untraced"` is part of every evaluation's identity.

Rather than change engine evaluation code, `traces.py`:
- runs the matrix through the unchanged `EvaluationService` path, exactly as E2–E5 did;
- re-executes each completed cell through the same `test_agent` call, with the same arguments, except `trace=True` and a scratch directory;
- **accepts the trace only if the re-execution reproduces the evaluated cell**: the same replay bytes, `match_id` and `result_id`. The trace's own binding record is checked again at extraction. Any difference is a hard stop.

**Reproductions, not observations.** The research lead approved this route on the condition that the traced execution is only a verification reproduction. The matrix has **11,520 registered cells**, and there are **at most 11,520 trace-verification reproductions**. A reproduction never enters a payoff, bootstrap, outcome or rate denominator:
- payoffs, hypotheses, flags, kill criteria and the bootstrap read only the evaluated cells (`run_e6.condition_data`, from each field's `experiment_result.json`);
- the telemetry a reproduction yields describes the one registered cell it reproduces, keyed by that cell's schedule ID;
- a duplicate trace record for one cell is rejected (`traces.records_by_schedule`).

Freeze v2 carries this as its `trace_verification` identity block. There is no engine change for trace mode. Tracing does not perturb a match: I-0 checked traced against untraced runs byte for byte. The cost is a second execution per cell, which is within plan §10's allowance of up to 2×.

### 3.2 Match validation also runs before agent code (plan §3.2, extended)

The plan puts the 2*d* < `arena_size` check in the controller `__init__`. It is there, and the same check also runs at the start of `from_python_entrants`, as a structured `match_configuration_invalid` error. That way an invalid match stops before any entrant is loaded or reset.

The evaluation layer adds no check of its own. An evaluation at arena 64 is inside the research-scale range, but every cell fails closed and no match is played; a test pins this. E6 itself runs only at A = 512.

### 3.3 Registration details

Both E6 identities are in the core-overlap guard, as their parents are. Otherwise a treatment would differ from its parent on overlapping cores.

`docs/AGENT_API_V2.md` documents the new context field, because AGENTS.md forbids changing wire shape silently.

### 3.4 The family (plan §5.2): fifteen details fixed at I-3

These are listed in [`tools/research/v6/e6/fixtures/README.md`](../../../tools/research/v6/e6/fixtures/README.md), and each is pinned by a behavior test. The research lead accepted them at Checkpoint A as implementation closure, now part of the frozen family specification.

**Amendment 1 corrected four of them before the v2 freeze** (A1 §4):
- **2, verification order:** probes now go outward from *a* + 1, where *a* is the last-known anchor.
- **3, an exhausted window:** a run that ends unconfirmed does not exhaust the window.
- **4, base finding:** a run of eight enemy beacons, or seven above a written anchor.
- **7, the next core cell:** a cyclic cursor carried across ticks.

The rest stand as fixed at I-3. The most consequential of those:
- **Hits.** A hit is `0xCE` owned by the opponent.
- **Values.** Every non-repair write writes `0x01`.
- **Timing.** A pending READ result is judged at the same process's next callback.
- **ADAPT.** The switch takes effect at the first callback of tick 17.

The manifests declare `search` and `posture` as `choice` parameters, not free strings, so an invalid value fails at resolution.

### 3.5 P-6 under the controls: resolved by amendment 1 (C-1)

The first version of this record raised it for review. Under a control Ruleset, an attacker whose first callback came after EVADER's first-callback MOVE adopted the moved anchor as the enemy core and never revised it. Attacks on EVADER therefore depended on seat. The research lead required the correction before I-7: unverified adoption only at the tick-1 first callback of the first mover, Seat A under every E6 Ruleset. See §4.

### 3.6 Analysis details

- **D-7 pairs mirrors through the family table.** E4's `mirror_pairs` relies on a `_twin` name suffix, and the tick-record comparison is E4's `tick_lines`, unchanged.
- **CQ-1 compares each cell's canonical callback-rows SHA-256.** That is equality of the streams, without holding 2,304 streams in memory.
- **Plan §7.2's "B = 1 when its denominator is empty" is superseded by the approved PR.** B is taken over the cells A counts, and A = 0 makes E6-H0 REFUTED through A.
- **Alternation (§6.2) calls E3's `analyze_actions` with no core-inferring names.** No E6 package follows the E2 inference contract.
- **D-1's re-derivation re-implements the documented rules independently:** offers, per-offer quotas, round-robin selection, disruption under both λ, and MOVE normalization. It agrees with the engine on scripted multi-process agents under all four E6 Rulesets. It fails, as it must, under the wrong radius, the wrong λ, an exclusive distance, or a tampered trace.

### 3.7 The one surviving I-4 mutant, and why it cannot matter

Mutant T6 made a READ inform its own telemetry row: it set `informed[entrant] = True` at the start of a READ row that hit an enemy core cell, instead of at the row's end. Within one row, `informed` is read only by the WRITE branch, which appends a D-4 record. A READ row never takes that branch, and the unmutated code sets `informed` at the end of the same row, so every later row sees the same value. The mutant also leaves `information_ticks` and `first_information` unchanged. So no telemetry field, no D-4 record, and therefore no registered value, gate verdict or interpretation can differ.

## 4. Checkpoint A: the First Review and Amendment 1

### 4.1 The first review (conditional pass)

The research lead approved:
- the engine mechanic, the analysis instrument and the family architecture;
- the trace route of §3.1, with its reproduction condition;
- the fifteen family details, as implementation closure;
- the smaller deviations: early radius validation, the core-overlap guard, D-7 through the family table, CQ-1 by digest, the PR over stale plan wording, and the API documentation;
- the I-4 survivor, provided this record keeps the exact reason (§3.7).

Seed generation was withheld until P-6 was corrected and the freeze regenerated.

### 4.2 Two more defects, found while qualifying the P-6 correction

The P-6 correction came with **engine-level behavior tests**: the family plays scripted, non-family opponents under the two control Rulesets only. Those tests assert the family's actions and record no outcome. The I-3 tests had driven the policy with hand-built observations only, so they could not show how the policy interacts with the engine's own write semantics. The engine tests found two defects, both already present in v1:
- **Verification could not confirm a stationary core.** The attack writes every visible enemy anchor first. A stationary anchor sits on core cell 0, the only stride-8 sample inside the core, so the attacker's own disruption erased it. A Seat B attacker made 265 READs over 40 ticks, none of which returned the enemy's `0xCE`, and it never wrote cells 1–7. Under the treatment the same held for every attacker except STEALTH.
- **Core cell 7 could starve.** The attack wrote "the first core cell in base order not yet written this tick", which was fixed detail 7. So whenever one of the eight offers went to disrupting an off-core anchor, cell 7 was never written. EVADER could not be captured once moved, and SPLIT, whose striker has 6 offers, never captured a core.

Both can change which registered row fires (A1 §2). Work stopped before any freeze, and the research lead decided:
- **P-6** as corrected;
- **the cyclic core cursor**, as proposed;
- **verification** with anchor + 1 sampling, but with the ambiguity between an anchor *on* core cell 0 and one *just below* the core resolved before the freeze. The overwritten anchor is a conditional stand-in for core cell 0, never a hit.
- **One amendment and one v2 re-freeze.** No v3, and no seeds: stop again at Checkpoint A.

### 4.3 The corrections (A1 §3)

- **C-1:** unverified adoption only at Seat A's tick-1 first callback. Seat A's tick-1 control forced line is unchanged, as is everything else in tick 1: an engine test compares it callback for callback with the v1 family.
- **C-2:** probes at *a* + 1 + 8*k*. A run of contiguous enemy beacons is grown down, then up. Eight beacons give the base. Seven give it only over an enemy anchor this entrant has successfully written. Anything else stays unconfirmed.
- **C-3:** a cyclic core cursor, carried across ticks and advanced only past a cell whose WRITE is chosen. A disruption still costs one of the eight offers.

### 4.4 Evidence

**Behavior tests** (`engine/tests/test_v6_e6_family.py`, 326 tests; I-3 had 135):
- **Synthetic, P-6:** Seat A adopts at its tick-1 first callback; Seat B never adopts unverified; the tick clause alone; Seat B finds an evader's real core rather than the moved anchor; no adoption under treatment visibility, in either seat, for all four search variants.
- **Synthetic, verification:** the stand-in over an overwritten core-0 anchor; an anchor one below the core, where the base is the cell above; a repaired core 0, where no stand-in is needed. Seven over a cell that is not a written anchor, seven over an anchor whose READ shows no applied own write, and six over a written anchor all stay unconfirmed. A written anchor that is not the last-known anchor stands in (SPLIT's two anchors).
- **Synthetic, cursor:** the omitted cell rotates 7, 6, 5, …, 0 over eight ticks of off-core disruption, and the idle action does not move the cursor.
- **Engine, under C-E6 and C-E6L:**
  - Seat A is the first mover under all four E6 Rulesets (scripted agents only).
  - Seat A adopts before the opponent acts, and its tick 1 is identical to v1's against four scripted opponents.
  - Seat B confirms a stationary core over its own overwritten anchor, with no core cell written before confirmation and no base off by one.
  - Seat B is not fooled by an anchor one cell below the core.
  - Seat B confirms a core whose cell 0 is repaired. The stand-in path is exercised under C-E6, and the repaired-beacon path under C-E6L.
  - Seat B never adopts an evader's moved anchor, and covers its real core.
  - Off-core disruption comes with seven distinct core cells whose omitted cell rotates, in both seats. At least two such ticks occur in every configuration except C-E6 Seat A, where the tick-1 forced line ends the match.
  - SPLIT reaches every core index from both seats.
  - CQ-1 is exact across RUSH, PACED, STEALTH and LURK against five scripted opponents, in both seats, under both controls.

**Behavior mutation:** 35 of 36 mutants killed. That is 17 against the three corrections, plus I-3's list re-run, re-pointed where A1 moved the text. The survivor, "a later probe hit restarts the run", is equivalent. While a run is open, verification issues only scan READs, and the search that issues probe READs requires that no run be open. Each entrant has one verifying process with at most one pending READ. So no verify or probe hit can arrive while a run is open.

### 4.5 For the review of v2

1. **The stand-in is any enemy anchor this entrant has written, not only the last-known anchor.** The research lead's wording named the last-known anchor. But the last-known anchor is the lowest visible address (fixed detail 1). A treatment attacker seeing both of SPLIT's anchors, with the sensor below the striker, would then never confirm SPLIT's core. The two-case analysis is unchanged by the widening, and a test pins it.
2. **One case the rule does not tell apart** (A1 §3, C-2). An anchor directly below a core whose top cell the entrant already holds would be taken for core cell 0. No family member can put its anchor there:
   - stationary anchors sit on core cell 0;
   - the searchers' anchors sit at base ± 64*k*;
   - one evasion moves an anchor by 8 to 64.

   So the case cannot arise in E6. Guarding against it would also block a confirmation that can occur, where the entrant's own paint sits just above the core.
3. **A correction to the Checkpoint A report.** It said ADAPT could put its anchor one cell below its own core. It cannot. ADAPT evades only after detecting damage, and detected damage permanently rules out its switch to hunting.

## 5. What Does Not Exist, and What Comes Next

No seed, no matrix cell, no family match under a treatment, no outcome of any kind, and no gameplay probe. The only matches the family has played are behavior tests against scripted, non-family opponents under the two control Rulesets. They assert actions and never record an outcome.

**Next is the research lead's Checkpoint A review of the v2 family and freeze**, including §4.5.

**After that, each separately authorized:**
1. **I-7:** `run_e6 generate-seeds --confirm-seed-generation`, then commit the v2 record's seed block, before any cell.
2. **Q:** the controls, one worker per field, then `qualify`.
3. **Checkpoint B.**
4. **T:** the treatment, the treatment gates, the frozen analysis, then the reveal and D-6, and only then the interpretation and the results record.
