# Bytefray V6 Phase 3 — Architecture & Context-Locality Review (3A-3L)

## A. Executive summary

Phase 3 asked one question: can a developer, or an AI coding agent, understand
and safely change one evaluation concept without loading the entire evaluation
subsystem into context? At the start of Phase 3, `agent_evaluation.py` was a
single 5,258-line module that mixed contracts, identity hashing, deterministic
planning, cell execution, the parallel-worker protocol, artifact/resume
persistence, run coordination, and CLI/presentation in one file. Phase 3
(sub-phases 3A through 3K, closed out by this 3L report) partitioned that
module into eight single-responsibility owners plus a permanent compatibility
facade, verified behavior-preserving at every step by differential testing
against the pre-extraction implementation, and left `agent_evaluation.py` at
263 lines of imports, re-exports, compatibility aliases, and one explicitly
retained piece of dead historical residue.

**Verdict: the primary Phase 3 decomposition program is complete.** No
remaining mixed live responsibility in `agent_evaluation.py` justifies a
further extraction (§K). Two behavioral characteristics discovered during the
program remain open as independent correctness questions, deliberately not
fixed here (§H). A small set of bounded, low-risk cleanup candidates remain,
also deliberately not repaired here (§I).

## B. Origin and scope

Phase 2's final qualification handed Phase 3 off explicitly
(`docs/research/v6/V6_PHASE2_FINAL_QUALIFICATION.md` §Z, "Phase 3
context-locality handoff"), naming `agent_evaluation.py` at **5,258 LOC** as
the primary candidate: "identify the seam between the sole current Ruleset-4
evaluation executor and historical v1/v2/group adapters." That handoff also
named `match_service.py`, the process-runtime modules, and `ruleset_policy.py`
as further candidates for a future locality study; Phase 3 as actually
executed scoped itself to the evaluation subsystem only; the others remain
unaddressed (see §M).

## C. Phase sequence and evidence

| Phase | Commit | Outcome |
|---|---|---|
| 3A | `d189293` chore(v6): sync architecture docs and remove orphan sources | Synced `ARCHITECTURE.md` to post-v4/v5 reality (398 lines changed) and removed two confirmed orphan sources (`client/src/renderers.py`, `engine/src/agents.py`) with no remaining reference anywhere in the tree. |
| 3B/3C | `597bf5c` test(v6): guard evaluation decomposition contracts | Added `test_evaluation_identity_contract.py` (475 lines: frozen identity-version goldens for versions 2-7) and `test_agent_evaluation_compatibility.py` (539 lines: the facade's 60-entry `__all__` and live non-`__all__` surface, plus two new strict-xfail tests stating the two known defects as desired invariants). This pair is simultaneously Phase 3B's characterization (confirming `agent_evaluation.py` as the hotspot and freezing what must not change) and Phase 3C's extraction guard (the safety net every later extraction commit was checked against). |
| 3D | `d32de2e` refactor(v6): extract evaluation contracts | Created `evaluation_contracts.py`: the low-level stable contracts and methodology vocabulary layer. |
| 3E | `d95ad47` refactor(v6): move evaluation aggregation to analysis | Moved foundational aggregate/comparison behavior into `evaluation_analysis.py`. |
| 3F | `74e9d60` refactor(v6): centralize evaluation identity | Created `evaluation_identity.py` as the one canonical identity-payload recipe (identity versions 2-7). Verified: 11/11 frozen identity goldens unchanged; a 6-methodology-case differential against the pre-extraction commit reproduced 6 evaluation IDs, 208 schedule IDs, and 208 condition fingerprints byte-identical; engine suite 2464 passed / 18 skipped / 2 xfailed. |
| 3G | `65faa52` refactor(v6): extract evaluation planning | Created `evaluation_planning.py`: placement/layout geometry and the deterministic matrix compiler. A ten-matrix full-record differential against 3F was byte-identical (order, geometry, path labels, schedule/condition/evaluation IDs). |
| 3H | `e948cf2` refactor(v6): extract evaluation cell execution | Created `evaluation_cell_execution.py`, giving "execute this already-planned cell exactly once" one canonical owner (`execute_cell`) shared by serial (`EvaluationService.run`) and parallel (`evaluation_worker`) dispatch — closing the genuine `EvaluationService` &lt;-&gt; `evaluation_worker` import cycle the worker used to escape via a function-local import and a throwaway `EvaluationService()` instance. Engine suite 2508 passed / 18 skipped / 2 xfailed; a ten-case baseline differential (serial, parallel, both orientation types, initialization failure, runtime failure, pre-/post-execution drift, resume, retry) was byte-identical. |
| 3I | `a416231` refactor(v6): extract evaluation artifact and resume | Created `evaluation_artifact.py`, consolidating four former `EvaluationService` methods (none of which touched `self`) and a dozen module-level helpers into one artifact-persistence/resume-trust owner. A twelve-scenario differential (including interruption, resume, no-op resume, retry, corrupted evidence, parallel interruption, revision reuse) was byte-identical. |
| 3J | `828e540` refactor(v6): extract evaluation service | Created `evaluation_service.py`, moving the canonical `EvaluationService` coordinator and its coordinator-only helpers (`_register_execution_context`, `_drift_detail`, `_drain_abandoned_cells`, `_evaluation_dispatcher_loop`) out of the facade. Full engine suite 2555 passed / 18 skipped / 2 xfailed; whole repository 3061 passed / 18 skipped / 3 deselected / 2 xfailed; client 504 passed / 3 deselected; ruff and mypy (engine and client) clean; `git diff --check` clean. |
| 3K | `8a757ed` refactor(v6): extract evaluation CLI | Created `evaluation_cli.py`, moving argument parsing, input resolution, and text/JSON presentation out of the facade. `agent_evaluation.py` fell from 1,341 LOC (its size immediately after 3J) to its final **263 LOC**. Verified against the Phase 3J baseline: unchanged help text, dry-run/text/JSON output, exit codes, and the full compatibility surface. |
| 3L | this closeout | Documentation/status synchronization only (this report, `ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/specs/agent_evaluation.md`); no production code changed except one stale in-code comment (see the 3L commit diff). |

Every extraction commit 3D-3K was checked, before being written, against the
Phase 3B/3C guard tests and a differential comparison to the immediately
preceding commit; none reports a behavior, timing, exception, matrix-order,
schedule-ID, identity, or artifact/resume change.

## D. Final ownership map

```text
evaluation_contracts            (low-level: stable identity/schema/orientation
        ^                        constants, EvaluationCell/Request/Result)
        |
evaluation_identity              (pure identity-payload construction, versions
        ^                        2-7; depends only on contracts)
        |
evaluation_planning              (EvaluationRequest -> ordered EvaluationCell
        ^                        matrix; consumes identity, executes nothing)
        |
evaluation_cell_execution        (execute_cell: run one already-planned cell;
        ^                        shared unchanged by serial + worker dispatch)
        |
evaluation_worker                (parallel-execution subprocess; depends only
                                   downward, never on EvaluationService)

evaluation_artifact              (artifact persistence + resume trust
        ^                        mechanics, independent of coordinator policy)
        |
evaluation_service               (EvaluationService: validates, freezes,
        ^                        dispatches, checkpoints, finalizes one run;
        |                        composes every module above plus analysis)
evaluation_cli                   (argument parsing, input resolution,
        ^                        presentation; calls EvaluationService)
        |
agent_evaluation                 (permanent compatibility facade: imports and
                                   re-exports; owns no evaluation behavior)
```

This diagram is conceptual, not a literal import chain (`evaluation_service`
imports every layer below it directly, not only its nearest neighbor). The
verified import edges are in §J.

Confirmed architectural facts:

- Contracts are low-level and import nothing else in the evaluation package.
- Identity does not depend on planning.
- Planning consumes identity; it does not hash anything itself.
- Serial and parallel (subprocess) execution share exactly one cell executor
  (`evaluation_cell_execution.execute_cell`).
- The worker does not call back into `EvaluationService` — the historical
  cycle Phase 3H closed.
- Artifact/resume mechanics are plain functions over explicit arguments,
  independent of `EvaluationService`'s own coordination policy.
- `EvaluationService` owns evaluation coordination and composes the modules
  below it; it does not import the CLI or the facade.
- `evaluation_cli` owns parsing/presentation and calls `EvaluationService`
  directly; it does not import the facade.
- `agent_evaluation` is the only module that imports the CLI, and it is the
  permanent compatibility facade, not an implementation owner.
- `evaluation_history` remains a separate reader/trust boundary: it adapts,
  discovers, and compares already-written `evaluation.json` artifacts, and
  never participates in the live-evaluation write path.

## E. The permanent compatibility facade

`battle_engine.agent_evaluation` is no longer the implementation owner of any
part of the evaluation subsystem. Its role is exactly:

- re-exporting the stable public surface (imports, never wrappers or
  subclasses — `agent_evaluation.main is evaluation_cli.main`,
  `agent_evaluation.EvaluationService is evaluation_service.EvaluationService`,
  and `agent_evaluation.build_matrix is evaluation_planning.build_matrix` all
  hold, verified live in this closeout);
- preserving every existing caller's import path, including `main`, the exact
  canonical `bytefray agents evaluate` CLI entry point;
- carrying the declared compatibility surface: an exact 60-entry `__all__`,
  plus a small set of live non-`__all__` attributes that grew over the
  program as later phases' repo-wide rescans found additional live callers
  (`LIFECYCLE_STATE_FINISHED`, `SCHEMA_VERSION_V4`,
  `STANDARD_V4_ARENA_SIZE`, `effective_conditions_payload`, `execute_cell`,
  among others — see `test_agent_evaluation_compatibility.py`);
- retaining one deliberately preserved piece of historical residue,
  `_cell_from_match_result_group`, documented in-module as dead for current
  production execution (see §I).

Internal implementation modules (the CLI, the service, evaluation history,
Designer workflows) import the canonical owners directly. External and
research callers may continue importing `battle_engine.agent_evaluation`
indefinitely — there is no migration requirement and none is implied by this
decomposition.

## F. Context-locality result

- `agent_evaluation.py` at the Phase 3B audit: **5,258 LOC** (matching the
  Phase 2 handoff's figure exactly).
- `agent_evaluation.py` after Phase 3K: **263 LOC**.
- Reduction: **4,995 LOC, approximately 95%**.

This is **not** a claim that Phase 3 deleted 95% of evaluation code — the
line count above measures one file, and the functionality that file used to
hold is fully present today, distributed across
`evaluation_contracts.py` (1,001 LOC), `evaluation_analysis.py` (821),
`evaluation_identity.py` (330), `evaluation_planning.py` (602),
`evaluation_cell_execution.py` (587), `evaluation_worker.py` (435),
`evaluation_artifact.py` (1,027), `evaluation_service.py` (1,070), and
`evaluation_cli.py` (1,135) — 6,988 lines of evaluation-coordination/execution
code across nine files that used to share one 5,258-line context, plus the
263-line facade.

The real improvement is **context locality**: a task scoped to "how is
identity computed," "what order does the matrix compile in," or "how does
resume trust work" now touches one module with a narrow, documented
responsibility and a small, verified set of upstream dependencies, instead of
requiring a reader (human or AI agent) to load a single 5,258-line file mixing
all of those concerns to find and safely change any one of them. The intended
benefits are smaller change surfaces per task, fewer unrelated dependencies
loaded per review, elimination of the `EvaluationService` &lt;-&gt;
`evaluation_worker` import cycle (and the lazy-import/throwaway-instance
workaround it forced), easier independent unit testing of each concern, and
clearer semantic ownership boundaries — not a smaller total quantity of code.

## G. Behavior preservation evidence

Accumulated across 3D-3K (see §C for the specific evidence at each phase):

- Frozen identity-version goldens (versions 2-7) pass unmodified throughout.
- Full-record matrix-planning differentials (order, geometry, path labels,
  schedule/condition/evaluation IDs) are byte-identical at every planning
  change.
- Serial/parallel cell-execution equivalence: a shared ten-case differential
  (serial, parallel subprocess, both orientations, initialization failure,
  runtime failure, pre-execution drift, post-execution drift, resume,
  retry-failed) is byte-identical.
- Artifact/resume semantic and byte comparisons across a twelve-scenario
  differential, plus an exact deterministic-fixture byte comparison (key
  ordering, indentation, cell ordering, trailing newline).
- CLI output differentials (help text, dry-run, text and `--json`
  presentation, exit codes) unchanged through the 3K CLI extraction.
- Full-repository qualification at the 3J/3K baseline: engine 2555 passed /
  18 skipped / 2 xfailed; client 504 passed / 3 deselected; whole repository
  3061 passed / 18 skipped / 3 deselected / 2 xfailed. Ruff and mypy (engine
  and client) clean; `git diff --check` clean.
- Both known behavioral defects (§H) remained strict `XFAIL` throughout —
  never silently fixed, never silently broken further.

## H. Known behavioral defects (not fixed by Phase 3)

These are independent correctness/contract questions, not unfinished
decomposition work, and Phase 3 does not close them. Both are enforced as
`pytest.mark.xfail(strict=True)` guards in
`engine/tests/test_agent_evaluation_compatibility.py`, so an accidental fix
would fail CI (XPASS) rather than pass silently.

1. **Scheduler override identity collision.** `scheduler_chunk_size` and
   `scheduler_rotate_start` reach execution (`test_scheduler_overrides_reach_...`
   passes) but do not change `evaluation_id`
   (`test_scheduler_overrides_that_change_execution_must_change_evaluation_identity`
   is a strict xfail): two evaluations with different scheduler overrides but
   otherwise-identical requests currently collide on the same identity.
2. **Preflight / run double freeze.** `preflight()` and `run()` each
   independently freeze/recompute evaluation identity from live agent source.
   When source is stable between the two calls the identities agree
   (`test_preflight_and_run_freeze_the_same_identity_when_source_is_stable`
   passes); when source changes between preflight and run, a
   preflight-addressed output directory can silently receive an artifact
   carrying a different `evaluation_id`
   (`test_preflight_addressed_output_must_not_silently_accept_a_different_run_identity`
   is a strict xfail).

Neither defect is an architectural blocker: both live entirely inside
`evaluation_service`/`evaluation_identity`'s already-established ownership
boundaries and do not require crossing module boundaries to fix.

## I. Deferred cleanup candidates (not repaired by Phase 3)

Recorded for future bounded cleanup, not repaired here:

- **Retired group-execution residue**, confirmed unreachable from current
  production execution:
  - `evaluation_planning._build_group_matrix` — called only by
    `test_evaluation_planning_matrix_equivalence.py`'s frozen-baseline
    equivalence guard, never by any production code path.
  - `agent_evaluation._cell_from_match_result_group` — zero callers anywhere
    in the tree (one docstring cross-reference from
    `evaluation_artifact.py`, not a call); the module's own comment already
    documents it as deliberately retained historical residue.
  - `evaluation_cell_execution._post_execution_identity_drift_group` — zero
    callers anywhere, including tests.

  This is distinct from the historical **group** vocabulary that remains
  live: `evaluation_group_analysis.py`, `evaluation_behavior.py`,
  `evaluation_capture.py`, and `evaluation_presets.py` are independent,
  actively-used sibling analysis modules (schemas, models, layouts,
  verification) predating Phase 3, not part of the retired execution
  residue above and not to be confused with it.

- **Duplicate `_safe_path_segment`.** A private path-sanitizing helper exists
  independently in both `evaluation_planning.py` and `agent_test.py`, with
  no shared owner.

- **Duplicate identity-construction responsibility.** Canonical evaluation
  identity hashing is owned by `evaluation_identity.py`, but
  `evaluation_cell_execution.current_execution_context` independently
  constructs its own `stable_id("evaluation-context", ...)` hash rather than
  going through `evaluation_identity`.

- **Stale in-code comment.** One comment in `evaluation_contracts.py`
  referenced `EvaluationService._execute_cell`, a name that stopped existing
  once Phase 3H moved cell execution to the module-level, public
  `evaluation_cell_execution.execute_cell`. Corrected in this closeout
  (comment-only; see the 3L commit) since it was clearly stale and could not
  affect execution. Historical narration of the same old name elsewhere
  (module docstrings and archived design docs describing what was true
  *before* Phase 3H, and a test docstring describing the same history) is
  accurate as written and was left alone.

None of these candidates individually or collectively rises to the level of
a "mixed live responsibility" hotspot (see §K); they are small, independently
bounded, and do not block closing the primary decomposition program.

## J. Dependency audit

A static AST import audit (this closeout) confirms every intended boundary
holds, with no exceptions:

```text
evaluation_contracts        -> (none)
evaluation_identity         -> evaluation_contracts
evaluation_planning         -> evaluation_contracts, evaluation_identity
evaluation_cell_execution   -> evaluation_contracts, evaluation_identity
evaluation_worker           -> evaluation_cell_execution, evaluation_contracts
evaluation_artifact         -> evaluation_contracts, evaluation_identity
evaluation_analysis         -> evaluation_contracts
evaluation_service          -> evaluation_analysis, evaluation_artifact,
                                evaluation_cell_execution, evaluation_contracts,
                                evaluation_identity, evaluation_planning,
                                evaluation_worker
evaluation_cli              -> evaluation_analysis, evaluation_contracts,
                                evaluation_planning, evaluation_service
agent_evaluation            -> evaluation_analysis, evaluation_artifact,
                                evaluation_cell_execution, evaluation_cli,
                                evaluation_contracts, evaluation_identity,
                                evaluation_planning, evaluation_service
```

No module imports anything above it in the intended ownership order; no
cycle exists; `evaluation_worker` never imports `evaluation_service` or
`agent_evaluation`; `evaluation_service` never imports `evaluation_cli` or
`agent_evaluation`; `evaluation_cli` never imports `agent_evaluation`.

## K. Reassessment of the remaining `agent_evaluation.py`

The 263-line facade's substantive content, by category:

- Module docstring: 11 lines, stating the facade's compatibility role.
- Imports/re-exports from the canonical owners: ~119 lines.
- Explicit compatibility aliases (module-level constant re-assignments for
  names not otherwise imported, e.g. `IDENTITY_VERSION_V4`,
  `LIFECYCLE_STATE_ABORTED`): ~17 lines.
- Deliberately retained dead historical residue
  (`_cell_from_match_result_group`), under its own labeled comment banner:
  ~44 lines including the banner and docstring.
- `if __name__ == "__main__"` dispatch: 2 lines.
- `__all__`: 62 lines, exactly 60 entries.

**Answer: no.** There is no remaining mixed live responsibility large enough
to justify another architectural extraction. The one non-trivial function
body left in the file is confirmed dead for production execution (§I), not
live logic mixed in with re-exports. Every other line is either an import, an
explicit compatibility alias, `__all__`, or the module docstring.

**Recommendation: close the primary Phase 3 decomposition program.**

## L. Context-locality assessment

- **Cohesion.** Each module now answers exactly one question (contracts:
  what are the stable vocabulary/shapes; identity: how is a payload hashed;
  planning: what order do cells execute in; cell execution: how does one
  cell run; artifact: how is state persisted/resumed/trusted; service: how
  is a whole run coordinated; CLI: how is a run invoked/presented from the
  command line).
- **Dependency direction.** Strictly downward, verified by AST audit (§J);
  no cycles.
- **Task-local context.** A change to identity hashing, cell-execution
  mechanics, or CLI presentation each now touches one module plus its
  already-narrow declared dependencies, not the former 5,258-line monolith.
- **Test locality.** Each extraction phase added or moved tests to the
  module that now owns the behavior under test (e.g., the cell-execution
  guard tests moved off private `EvaluationService` monkeypatch seams onto
  the canonical `execute_cell` owner in Phase 3H).
- **Service/CLI and worker/service separation.** Both hold with no back-edge
  (§D, §J); the historical `EvaluationService` &lt;-&gt; `evaluation_worker`
  cycle Phase 3H closed was the last such edge in the subsystem.
- **Historical trust boundaries.** `evaluation_history` remains a separate,
  Qt-free reader/adapter package over already-written artifacts, unaffected
  by which module inside `battle_engine` currently produces them.
- **Facade stability.** The 60-entry `__all__` and every characterized live
  non-`__all__` attribute were re-verified unchanged at every phase and
  again in this closeout (§E).

## M. Recommendation after Phase 3

The evaluation-subsystem decomposition Phase 2 handed off is complete and
should not be reopened for further extraction (§K). Two independent
correctness questions remain open by design (§H) and one small, bounded set
of cleanup candidates remains unrepaired (§I) — neither blocks closing this
program.

The Phase 2 handoff separately named `match_service.py` (1,126 LOC at that
time), the process-runtime modules, and `ruleset_policy.py` as further
locality candidates; Phase 3 did not touch them, and no evidence gathered
during this closeout suggests any of them mixes responsibilities the way
`agent_evaluation.py` did. Whether they warrant a future, separately
authorized locality pass is a question for whoever picks up that thread next,
not a continuation of this Phase 3 program.
