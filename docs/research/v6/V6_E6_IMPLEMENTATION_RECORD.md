# Bytefray V6 E6 — Priced Sensing: Implementation Record (Checkpoint A)

**Status: IMPLEMENTED THROUGH I-6, AWAITING CHECKPOINT A.** This records what phases I-0 to I-6 of the [implementation plan](V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md) built. It covers where the implementation had to settle something the plan did not, the details that need the research lead's review, and the evidence behind each phase.
- **What exists:** no seed has been generated, no matrix cell has run, and no family member has played under a treatment Ruleset.
- **What remains:** seed generation (I-7), the controls (Q) and the treatment (T) each need separate authorization.

**Branch:** `v6-research`
**Date:** 2026-09-25
**Governing records:**
- [pre-registration](V6_E6_PRICED_SENSING_PREREGISTRATION.md) (**PR**);
- [implementation plan](V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md) (**plan**);
- [design review](V6_PRICED_SENSING_DESIGN_REVIEW.md) (**DR**).

---

## 1. Identities

| Identity | Value |
|---|---|
| Structural matrix identity | `v6-e6-matrix-v1-cd040eac42ef` (structural digest `cd040eac42ef6554f3d6c0faf4a7fbe83dd963d416cfad8e7f9c4aa8630f13a6`). No seed values. |
| Pre-registration transcription | `tools/research/v6/e6/preregistration.json`, SHA-256 `e1ccc1cc7ef2f3b193019590984b9f34fafb0b7e176b1f4ebb8387d0566ee5f4` |
| Analysis freeze | `v6-e6-freeze-v1-428033032ce2`, tooling qualified at `5f93381`. The record is `tools/research/v6/e6/analysis_freeze.json`. |
| Seed commitment and execution identity | **PENDING.** These slots in the freeze record are filled only at I-7, before the first matrix cell. |
| Control qualification | **PENDING.** Filled after Q. The treatment unlock requires it. |

## 2. Phases and Commits

| Phase | Commit(s) | Content |
|---|---|---|
| I-0 | `ddf0eda` | Parent byte-identity freeze of `research-scale` and `disruption-slot1`: 84 matches, 86 tests. Committed before any engine change. |
| I-1 | `e0625a1`, `5ea1152` | `RulesetPolicy.detection_radius` and `resolve_sensing_radius`; the one visibility line; match-level validation; the two Ruleset identities and their registration. 128 dedicated tests; 10 of 10 mutants killed. |
| I-2 | `aa19daf` | `MatchContextV2.detection_radius` under the direct and the worker executors and in validation; `docs/AGENT_API_V2.md`. 39 tests; 7 of 7 mutants killed. |
| I-3 | `0b34c0c` | 18 family packages, the member table, opaque IDs, fingerprints and the D-5 gate. 135 tests; 20 of 20 behavior mutants killed. |
| I-4 | `c03ea70` | Bound trace capture, compression, retention and the compact-telemetry extractor. 26 tests; 11 of 12 mutants killed. The survivor is equivalent: a row is either a READ or a WRITE, so no D-4 record can differ. |
| I-5 | `596857a` | Payoffs, bootstrap, hypotheses, flags, kill criteria, interpretation, D-1 re-derivation, the gates, the descriptive sections and the seed tooling. 93 tests; 25 of 25 mutants killed. |
| I-6 | `5f93381` and this commit | Structural matrix, pre-registration transcription, analysis freeze, runner, this record, ROADMAP and FUTURE_PLANS. 44 tests. |

End of implementation, with this record in place: the full suite gave 5209 passed, 18 skipped, 3 deselected. `mypy` is clean on engine (97 files) and client (16 files), and `ruff check .` passes. All E6 test files together: 551 tests.

## 3. Where the Implementation Settles What the Plan Did Not

Each item below was fixed before any E6 data existed. **Items 3.1 and 3.2 change how a plan step is carried out.** The rest settle details the plan left open.

### 3.1 Trace capture is a bound re-execution (plan §6.1, corrected)

Plan §6.1 says the runner sets `MatchRequest.trace_path` for each cell. It cannot through the evaluation path:
- `EvaluationService` runs each cell through `execute_cell`, which calls `agent_test.test_agent(trace=False)`;
- `tracing: "untraced"` is part of every evaluation's identity.

Rather than change engine evaluation code, `traces.py`:
- runs the matrix through the unchanged `EvaluationService` path, exactly as E2–E5 did;
- re-executes each completed cell through the same `test_agent` call, with the same arguments, except `trace=True` and a scratch directory;
- **accepts the trace only if the re-execution reproduces the evaluated cell**: the same replay bytes, `match_id` and `result_id`. The trace's own binding record is checked again at extraction. Any difference is a hard stop.

Tracing does not perturb a match: I-0 checked traced against untraced runs byte for byte. The cost is a second execution per cell, which is within plan §10's allowance of up to 2×. The alternative is an engine change that adds a traced evaluation mode, and so a new evaluation identity. It is available if the research lead prefers it.

### 3.2 Match validation also runs before agent code (plan §3.2, extended)

The plan puts the 2*d* < `arena_size` check in the controller `__init__`. It is there, and the same check also runs at the start of `from_python_entrants`, as a structured `match_configuration_invalid` error. That way an invalid match stops before any entrant is loaded or reset.

The evaluation layer adds no check of its own. An evaluation at arena 64 is inside the research-scale range, but every cell fails closed and no match is played; a test pins this. E6 itself runs only at A = 512.

### 3.3 Registration details

Both E6 identities are in the core-overlap guard, as their parents are. Otherwise a treatment would differ from its parent on overlapping cores.

`docs/AGENT_API_V2.md` documents the new context field, because AGENTS.md forbids changing wire shape silently.

### 3.4 The family (plan §5.2): fifteen details fixed at I-3

These are listed in [`tools/research/v6/e6/fixtures/README.md`](../../../tools/research/v6/e6/fixtures/README.md), and each is pinned by a behavior test. The most consequential:
- **Verification order.** Reads go outward from the last-known anchor (17 READs), and an exhausted window forgets the anchor.
- **Base finding.** A downward scan with an 8-cell cap.
- **Hits.** A hit is `0xCE` owned by the opponent.
- **Values.** Every non-repair write writes `0x01`.
- **Timing.** A pending READ result is judged at the same process's next callback.
- **ADAPT.** The switch takes effect at the first callback of tick 17.

The manifests declare `search` and `posture` as `choice` parameters, not free strings, so an invalid value fails at resolution.

### 3.5 For review: what P-6 implies under the controls

Approved decision P-6 keeps unverified adoption at the first callback. Under a **control** Ruleset, an attacker whose first callback comes after an EVADER's first-callback MOVE sees one anchor. If that anchor lies at least 64 cells from the attacker's own core, the attacker adopts it as the enemy core base, although it is 8–64 cells from EVADER's real core, and never revises it.

So under the controls an attacker's forced line against EVADER depends on seat:
- it usually works when EVADER is Seat B;
- it usually fails when EVADER is Seat A.

This follows directly from the approved rule. It never fires under a treatment, and it is the E2–E5 fixture convention. It shapes the control payoff table, and with it E6-H1C, E6-H0 and the PF comparisons, so it is raised here while the experiment is still blind to its seeds.

### 3.6 Analysis details

- **D-7 pairs mirrors through the family table.** E4's `mirror_pairs` relies on a `_twin` name suffix, and the tick-record comparison is E4's `tick_lines`, unchanged.
- **CQ-1 compares each cell's canonical callback-rows SHA-256.** That is equality of the streams, without holding 2,304 streams in memory.
- **Plan §7.2's "B = 1 when its denominator is empty" is superseded by the approved PR.** B is taken over the cells A counts, and A = 0 makes E6-H0 REFUTED through A.
- **Alternation (§6.2) calls E3's `analyze_actions` with no core-inferring names.** No E6 package follows the E2 inference contract.
- **D-1's re-derivation re-implements the documented rules independently:** offers, per-offer quotas, round-robin selection, disruption under both λ, and MOVE normalization. It agrees with the engine on scripted multi-process agents under all four E6 Rulesets. It fails, as it must, under the wrong radius, the wrong λ, an exclusive distance, or a tampered trace.

## 4. What Does Not Exist, and What Comes Next

No seed, no matrix cell, no family match under a treatment, no outcome of any kind, and no gameplay probe. The only matches any family member has played are the control-Ruleset smoke tests, which assert that no action is invalid or forfeited and record no outcome.

**At Checkpoint A the research lead reviews:**
- the implementation, and in particular §3.1 (the trace route) and §3.5 (P-6 under the controls);
- whether to authorize I-7.

**After that, each separately authorized:**
1. **I-7:** `run_e6 generate-seeds --confirm-seed-generation`, then commit the freeze record's seed block, before any cell.
2. **Q:** the controls, one worker per field, then `qualify`.
3. **Checkpoint B.**
4. **T:** the treatment, the treatment gates, the frozen analysis, then the reveal and D-6, and only then the interpretation and the results record.
