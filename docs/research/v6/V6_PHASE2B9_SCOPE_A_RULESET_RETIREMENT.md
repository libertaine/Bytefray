# Bytefray V6 — Phase 2B.9: Scope A Ruleset Retirement

**Phase type:** Implementation. Retires the three Class-1 closed-research
ruleset identities identified by Phase 2B.8's audit
(`docs/research/v6/V6_PHASE2B8_LEGACY_RULESET_RETIREMENT_AUDIT.md`) from
executable registration, while preserving their historical recognition in
full. Implements exactly Scope A of that audit's three-scope plan; Scopes B
and C are explicitly out of scope and untouched.

**Governing distinction, restated:** closed research behavior is retired;
historical knowledge is retained.

---

## A. Baseline

Established before any change, per the charter's §3:

| Check | Result |
| --- | --- |
| Branch | `v6-research` — confirmed |
| HEAD SHA | `b55b8ea49019bd3ca5f1710b79fd4dfe5b6be24c` |
| Phase 2B.7/2B.8 reports | Committed in HEAD (`git show --stat HEAD` — both files present, 2,473 insertions, no other changes) |
| Working tree at phase start | Clean (`git status --short` empty) |
| Divergence from `origin/v6-research` | 0 ahead, 0 behind (`git fetch origin v6-research main` then `git rev-list --left-right --count`) |
| `main` | `82549f9c3ccbdb2e13b8165b32afef00def4a8f2`, identical to `origin/main` — untouched throughout |
| Canonical tests collected | **3,713** across 158 files (summed from the per-file collection reporter) — exact match to the charter's expected baseline |

HEAD and the working tree were re-verified unchanged (`git rev-parse HEAD`,
SHA-256 digests of every phase-critical source file) immediately before and
immediately after the final qualification run (§O); both checks matched
exactly, confirming no external process mutated the checkout during
qualification.

---

## B. Scope implemented

**Scope A only**, per the charter. Retired from executable registration:

* `bytefray-rules-2-alpha1`
* `bytefray-rules-2-alpha11`
* `bytefray-rules-3-alpha1`

Left untouched and fully executable: `bytefray-rules-1`, `bytefray-rules-2`,
`bytefray-rules-4-alpha1`, `bytefray-rules-4-alpha2`, `bytefray-rules-4`.
`bytefray-rules-4` remains the frozen V6 research control.

Scope B (V4 alphas), Scope C (Agent API v1/VM retirement), and the four
Ruleset-1-fallback repairs (T-1/T-2/T-3/T-11) were explicitly left alone,
per the charter's §12/§13/§25 boundaries — see §R for what those later
phases inherit from this one.

---

## C. Ruleset-2 promotion proof conversion

Per the charter's §2, `bytefray-rules-2-alpha11`'s executable registration
could not be removed until its promotion-equivalence proof
(`engine/tests/test_ruleset_v2_promotion_equivalence.py`, 12 collected
cases: 11 scenario cases + 1 differentiation case) was converted from a live
two-ruleset comparison into a frozen-golden characterization. Done **before**
any registry edit, in this order:

1. **Original corpus re-confirmed passing.** A scratchpad generator script
   (not committed) reused this file's exact pre-conversion scenario corpus
   and helper functions, ran each of the 11 scenarios under
   `bytefray-rules-2-alpha11` **and** `bytefray-rules-2` while both were
   still fully registered, and asserted the full semantic snapshot (winner,
   ticks, termination, per-agent stat tuple, final arena bytes, final
   ownership, complete ordered event stream) was identical between the two
   — reproducing the file's own pre-existing assertions from scratch. All 11
   passed.
2. **Golden derived from the confirmed-passing baseline.** For each
   scenario, the alpha11-side snapshot (the one just proven equal to v2's)
   was hashed (SHA-256 of a canonical JSON encoding) and its summary fields
   (winner, ticks, termination reason, score, agent ids) recorded. The
   differentiation scenario's alpha1-side arena content (core cells at the
   documented blank byte) was captured the same way.
3. **New characterization confirmed passing.** The rewritten test file —
   same scenario corpus, now module-level and shared, running only under
   `bytefray-rules-2` and comparing against the frozen `EXPECTED` table —
   was run standalone: **12/12 passed.**
4. **Drift-sensitivity demonstrated.** `python_runtime.CORE_BEACON_BYTE` was
   temporarily changed from `0xCE` to `0xCF` (a one-bit mutation to real
   gameplay behavior, reverted immediately after), and the golden test file
   was re-run: **all 11 scenario cases failed** on digest mismatch,
   confirming the characterization actually detects behavioral drift rather
   than passing vacuously. The revert was verified with `git diff --stat`
   (empty) and a clean re-run (39/39 passed, combined with the unrelated
   `test_v4_stable_ruleset_equivalence.py` control file run in the same
   pass).

The differentiation test (`test_permanent_v2_still_differs_from_ruleset_v1_and_alpha1`,
renamed `..._and_frozen_alpha1`) was converted the same way: `bytefray-rules-1`
stays live (still executable), `bytefray-rules-2-alpha1`'s side is now the
already-current, still-retained `python_runtime.CORE_SEED_BYTE_ALPHA1`
constant rather than a live run, and `bytefray-rules-2` stays live.

**Provenance recorded in the file itself:** the module docstring names the
exact commit the golden values were captured at
(`b55b8ea49019bd3ca5f1710b79fd4dfe5b6be24c`, immediately pre-retirement),
states the reproduction method (check out that commit's version of the
file, which still exercises alpha11 directly, and rerun it), and restates
the versioning policy copied from the precedent file
(`test_ruleset_v1_equivalence.py`): a legitimate Ruleset 2 gameplay/Agent
API/RNG/schema change must version `EXPECTED` deliberately, never refresh
it in place to make a regression pass.

Collected case count for this file: **12 → 12 (unchanged)** — converted,
not deleted, consistent with the charter's explicit instruction not to
simply remove this proof.

---

## D. Registry/policy changes

`engine/src/battle_engine/ruleset_policy.py`:

* Removed the `RULESET_V2_ALPHA1`, `RULESET_V2_ALPHA11`, `RULESET_V3_ALPHA1`
  policy objects and their three `_RULESET_POLICIES` entries.
* Removed their three `__all__` entries (the policy-object names only).
* **Kept** all three `BYTEFRAY_RULESET_*_ID` string constants, still
  exported in `__all__`, for historical recognition.
* Updated the module's own prose (the `_RULESET_POLICIES` docstring, the
  `RULESET_V2`/`RULESET_V4` promotion-pattern comments referencing alpha11)
  to state the retirement and point at its replacement evidence rather than
  describing three now-nonexistent live objects.

`engine/src/battle_engine/agent_evaluation.py`:

* Removed `BYTEFRAY_RULESET_V3_ALPHA1_ID` from `_V2_METHODOLOGY_RULESET_IDS`.
* Removed it from the `_validate` evaluation-ruleset allow-list (and its
  error-message enumeration).
* Rewrote the `locality_reach` validation guard: since `has_bounded_locality`
  is gone (§E) and no Ruleset can ever satisfy it again, the guard now
  unconditionally rejects any non-`None` `locality_reach` with a clear,
  honest `EvaluationConfigurationError` naming the retirement, instead of
  naming a Ruleset ID that can no longer be selected.
* Simplified `EvaluationRequest.resolved_locality_reach` to unconditionally
  return `None` (previously resolved through the now-removed
  `has_bounded_locality`/`DEFAULT_LOCALITY_REACH`).

**Behavioral verification** (direct execution against the modified tree):

```
registered: ['bytefray-rules-1', 'bytefray-rules-2', 'bytefray-rules-4',
             'bytefray-rules-4-alpha1', 'bytefray-rules-4-alpha2']
bytefray-rules-2-alpha1   -> UnknownRulesetError OK
bytefray-rules-2-alpha11  -> UnknownRulesetError OK
bytefray-rules-3-alpha1   -> UnknownRulesetError OK
bytefray-rules-1          -> resolves OK
bytefray-rules-2          -> resolves OK
bytefray-rules-4-alpha1   -> resolves OK
bytefray-rules-4-alpha2   -> resolves OK
bytefray-rules-4          -> resolves OK
ID constants still present: bytefray-rules-2-alpha1 bytefray-rules-2-alpha11 bytefray-rules-3-alpha1
```

No retired ID maps to `bytefray-rules-2` or `bytefray-rules-4` anywhere
(T-12) — confirmed both structurally (no such mapping was added) and by
test (`test_v6_phase2b9_scope_a_retirement.py`, §I).

`_CORE_PLACEMENT_GUARDED_RULESET_IDS` (`match_service.py`) had
`bytefray-rules-3-alpha1` removed — dead membership, since the guard is
unreachable for an ID `resolve_ruleset_policy` already rejects.
`VULNERABLE_CORE_RULESET_IDS`/`OBSERVABLE_CORE_RULESET_IDS` were **not**
touched (§H).

---

## E. Unique production implementation removed

`python_runtime.py`'s entire v3-Phase-2 bounded-locality mechanic — the
only executable consumer of which was `bytefray-rules-3-alpha1` — was
removed as dead code:

* `LOCALITY_RULESET_IDS`, `DEFAULT_LOCALITY_REACH`, `has_bounded_locality`
* `circular_distance`, `circular_displacement` (locality-only; distinct
  from `placement._circular_distance` and `spectator_events.circular_distance`,
  neither of which was touched)
* `PythonEntrantState`'s `locus` field and ten `locality_*` telemetry fields
  (state that could now never become non-default)
* `ABSOLUTE_ADDRESSING_ACTIONS` and `validate_action`'s `locality` parameter
  (the three locality action kinds are now rejected unconditionally by the
  same "unsupported action" path every other unrecognized action already
  used — **`LOCALITY_ACTIONS` itself, and its rejection guard, were kept
  verbatim**, per the charter's explicit instruction, since
  `ActionKind.MOVE`/`LOCAL_READ`/`LOCAL_WRITE` must stay defined for
  historical replay/trace deserialization)
* `apply_action`'s `locality_reach` parameter and its locality dispatch
  branch; `_apply_locality_action`, `record_locality_tick`,
  `locality_statistics` (whole functions)
* `PythonEntrantController`'s locus-seeding logic and its per-tick
  `record_locality_tick` call

`PythonEntrantController`/`SupervisedPythonEntrantController` **keep**
their `locality_reach` constructor parameter, now unconditionally resolving
to `self.locality_reach = None` regardless of input — deliberately, so that
`match_service.py`'s two construction call sites,
`agent_worker.py`/`evaluation_worker.py`'s subprocess wire plumbing, and
`agent_test.py`'s request chain (all outside the audit's measured Scope-A
file list) need **no changes**: they already pass a value that was "ignored
unless the Ruleset supports it" before this phase, and now always ignore
it, which is the same contract with the one remaining case collapsed away.
This mirrors `_resolve_locality_reach`/`resolved_locality_reach` in
`match_service.py`/`agent_evaluation.py`, both simplified to unconditional
`None`-returning seams rather than deleted, for the same reason.

`match_service.py`: `_build_python_result`'s `locality_reach` parameter and
its "locality" research-metadata block (the only remaining hard dependency
on the deleted `locality_statistics`) were removed, along with the one
call-site kwarg that supplied it. `MatchRequest.locality_reach` the field
itself was **kept** (same "kept but permanently inert" reasoning as the
controllers above).

`agent_api.py`: the `ActionKind.MOVE`/`LOCAL_READ`/`LOCAL_WRITE` comment
block was corrected — it previously claimed `validate_action` "accepts them
only under `bytefray-rules-3-alpha1`," which is no longer true (nothing
accepts them now); the comment now states the rejection is unconditional
and explains why the members are still defined.

**Measured production LOC**, `git diff --stat` across the six touched
source files (`agent_api.py`, `agent_evaluation.py`, `match_service.py`,
`python_runtime.py`, `ruleset_policy.py`, `supervised_runtime.py`):

```
6 files changed, 175 insertions(+), 558 deletions(-)
```

**Net −383 LOC.** The charter's own estimate was "approximately ~318,"
explicitly flagged as needing measurement rather than being trusted; the
actual figure is higher because this implementation did a complete removal
of the locality dispatch/validation/state machinery (including the
`PythonEntrantState` fields and `apply_action`'s dead branch) rather than a
partial one, and because several removed multi-paragraph design-rationale
comments were replaced with shorter retirement notices (net insertions
include those replacement comments, provenance text, and the frozen-golden
table in the promotion-equivalence file is counted separately, in §G).

---

## F. Research tools/fixtures removed

| Path | Kind | LOC |
| --- | --- | ---: |
| `tools/v3_phase2_locality_corpus.py` | research driver | 712 |
| `tools/v3_phase2_locality_rubric.py` | research driver | 783 |
| `engine/src/battle_engine/data/v3_locality_agents/` (6 agent dirs, 12 files: `agent.py`+`agent.yaml` each) | fixtures | 1,660 (agent files) |
| `engine/src/battle_engine/data/benchmarks/v3_phase2_locality.json` | corpus | (data) |
| `engine/src/battle_engine/data/benchmarks/v3_phase2_locality_corpus.json` | corpus | (data) |

Zero remaining importers confirmed (`git grep` for each removed path/module
name, repo-wide, before deletion). Combined tools+fixtures removal:
**16 files, 3,164 LOC** of research-only material (1,495 tools + 1,669
fixtures/agents, per `git diff --stat`).

---

## G. Tests removed/pruned

### Whole-file removals (11 files, the charter's §8 list)

| File | Cases |
| --- | ---: |
| `test_ruleset_v2_alpha1.py` | 19 |
| `test_ruleset_v2_alpha11.py` | 37 |
| `test_v2_alpha1_reference_agents.py` | 9 |
| `test_v2_alpha2_reactive_defender.py` | 15 |
| `test_v2_alpha4_1_winner_semantics.py` | 12 |
| `test_v2_alpha4_multi_entrant.py` | 10 |
| `test_v2_alpha8_core_tracker.py` | 24 |
| `test_v3_preflight_characterization.py` | 3 |
| `test_v3_phase2_locality_agents.py` | 70 |
| `test_v3_phase2_locality_evaluation.py` | 22 |
| `test_v3_phase2_locality_runtime.py` | 64 |
| **Total** | **285** |

(5,414 LOC removed across these 11 files, per `git diff --stat`.)
`test_ruleset_v2_promotion_equivalence.py` — the 12th file the charter's §8
names — was **converted**, not deleted (§C), so it is excluded from this
total; the charter's own "297" figure for this batch includes those 12
cases, this report's "285" excludes them, and the two numbers reconcile
exactly (297 − 12 = 285).

### Mixed-file pruning (case-by-case, per the charter's §9)

| File | Before | After | Δ | What changed |
| --- | ---: | ---: | ---: | --- |
| `test_ruleset_policy.py` | 49 | 47 | −2 | Removed `test_v2_alpha1_ruleset_id_resolves_to_its_own_distinct_policy` and `test_v2_alpha1_scheduling_and_termination_are_identical_to_v1` (both executed the removed `RULESET_V2_ALPHA1` object directly); pruned alpha1/alpha11 assertions from `test_permanent_v2_ruleset_id_resolves_to_its_own_distinct_policy`, kept its V1/V2 distinctness assertion |
| `test_ruleset_v2.py` | 16 | 17 | +1 | Replaced `test_all_four_identities_resolve_to_four_distinct_policy_objects` (called `resolve_ruleset_policy` on both alphas) with `test_v1_and_v2_resolve_to_distinct_policy_objects` (V1/V2 only) **and** a new `test_retired_alpha_identities_no_longer_resolve` (both alphas raise `UnknownRulesetError`); fixed `test_permanent_v2_is_not_an_alias_of_alpha11_or_anything_else`'s final assertion (was a same-object-identity check via live resolution, now a `pytest.raises(UnknownRulesetError)` check, keeping its `normalize_ruleset_id` assertions unchanged) |
| `test_ruleset_v2_runtime_compatibility.py` | 17 | 15 | −2 | `test_v1_and_alpha_policies_are_unrestricted` (parametrized `[V1, ALPHA1, ALPHA11]`) narrowed to V1-only, since the alpha cases called `resolve_ruleset_policy` directly; `test_alpha_identities_still_dispatch_successfully_on_vm` (parametrized `[ALPHA1, ALPHA11]`, asserted VM dispatch succeeded) rewritten to `test_retired_alpha_identities_no_longer_dispatch_even_on_vm` (asserts `UnknownRulesetError`, no artifact written) — same 2 parametrized cases, opposite assertion |
| `test_v2_default_placement.py` | 28 | 28 | 0 | `test_historical_alpha_identities_keep_v1_style_zero_defaults` renamed/reworded to `test_retired_alpha_identities_still_get_the_masked_zero_default`, same assertion (`resolve_direct_match_starts` fails **safe**, not closed — T-4 finding, verified by direct execution, see §note below) with corrected rationale; `test_historical_alpha_identities_are_not_gated_by_the_v2_overlap_guard` rewritten to `test_retired_alpha_identities_fail_closed_before_any_overlap_guard_question` (asserts `NativeMatchService.run` now raises `UnknownRulesetError` before any artifact write, superseding the now-moot "not gated by the overlap guard" question) |
| `test_v4_alpha2_placement.py` | 67 | 67 | 0 | One parametrize row's expected value changed: `(BYTEFRAY_RULESET_V3_ALPHA1_ID, "seat_spread")` → `(BYTEFRAY_RULESET_V3_ALPHA1_ID, "zero")`, with a comment explaining the masked fail-safe default (same T-4 finding) |
| `test_v4_interleaved_scheduler.py` | 14 | 14 | 0 | Removed the `policy_v3 = resolve_ruleset_policy(BYTEFRAY_RULESET_V3_ALPHA1_ID)` line and its now-moot `scheduler_mode == "sequential"` assertion from `test_ruleset_policy_dispatch_modes`; removed the now-unused import |
| `client/tests/test_replay_status.py` | 22 | 22 | 0 | `test_real_alpha1_core_derived_without_beacon_assumption` and `test_real_alpha11_and_v2_both_work_and_stay_distinct` re-pointed at frozen fixture replays (§H) instead of live `NativeMatchService` execution under alpha1/alpha11; v2's side stays live |
| `test_ruleset_v2_promotion_equivalence.py` | 12 | 12 | 0 | Converted (§C) |

**T-4 note.** `placement.core_placement_mode` deliberately fails *safe* to
`"zero"` for any unregistered Ruleset ID (its own docstring says so) rather
than raising — real dispatch (`NativeMatchService.run`/`resolve_ruleset_policy`)
is meant to reject the identity first, before placement is ever consulted.
Both affected tests were rewritten to pin this precisely: the masked
`"zero"` fallback is unchanged and expected (not a regression), and a
*separate*, already-passing test in each of the two files proves the real
dispatch-level rejection that keeps the masked path from mattering in
practice (`test_retired_alpha_identities_fail_closed_before_any_overlap_guard_question`,
`test_retired_alpha_identities_no_longer_dispatch_even_on_vm`).

### New file

`test_v6_phase2b9_scope_a_retirement.py` — **19 cases** (§I).

### Reconciliation

Net collected-case change: −285 (whole-file) − 2 (`test_ruleset_policy.py`)
+ 1 (`test_ruleset_v2.py`) − 2 (`test_ruleset_v2_runtime_compatibility.py`)
+ 19 (new file) = **−269**. Baseline 3,713 − 269 = **3,444**, matching the
independently re-verified final collection total exactly. This also
accounts for `test_ruleset_v2_promotion_equivalence.py` and the
`test_v2_default_placement.py`/`test_v4_alpha2_placement.py`/
`test_v4_interleaved_scheduler.py`/`client/tests/test_replay_status.py`
files, all of whose *case counts* are unchanged even though their *content*
was rewritten (§C, this table). See §N for the checkpoint-by-checkpoint
collection log this arithmetic is built from.

---

## H. Historical-recognition coverage retained

Verbatim, unmodified (confirmed by `git diff --stat` showing no diff):

* `BYTEFRAY_RULESET_ID`, `normalize_ruleset_id`, `rules._RULESET_ALIASES`
  (`rules.py` untouched)
* `resolve_result_ruleset` / `resolve_replay_ruleset`, including their
  `"recovered"` branches (`result_model.py`, `replay.py` untouched)
* `VULNERABLE_CORE_RULESET_IDS` / `OBSERVABLE_CORE_RULESET_IDS`
  **memberships** for all three retired identities (T-9) — only the
  now-orphaned `_CORE_PLACEMENT_GUARDED_RULESET_IDS` entry for
  `bytefray-rules-3-alpha1` was removed (§D), never these two tables
* `has_vulnerable_core`, `has_observable_core` (still callable, still
  correct for all three retired IDs — verified in §I)
* `ActionKind.MOVE`/`LOCAL_READ`/`LOCAL_WRITE`, `LOCALITY_ACTIONS`,
  `MatchContext.locality_reach`, `Observation.locus` (`agent_api.py`'s
  dataclass fields untouched; only a stale comment was corrected, §E)
* `_readable_ruleset` / `ruleset_label` (`app/services/replay_history_presentation.py`,
  untouched — shape-derived, no table, no registry coupling) and
  `resolve_match_ruleset_label` (`client/src/battle_client/replay_status.py`,
  untouched)
* `test_v5_replay_history_presentation.py`, `test_ruleset_persistence.py`,
  `test_result_model.py`, `test_rules.py`, `test_replay_history.py`,
  `test_evaluation_history_comparison.py`, `client/tests/test_hud_layout.py`,
  `client/tests/test_playback_controller.py` — **all byte-for-byte
  unmodified** (`git diff --stat`: no diff for any of them), all passing in
  the final full-suite run (§O)

`client/tests/test_replay_status.py` was modified but **re-pointed, not
deleted** (§G): its two real-match-execution cases for alpha1/alpha11 now
load frozen fixture replays
(`client/tests/fixtures/replay_status/alpha1_attack_replay.jsonl`,
`alpha11_no_attack_replay.jsonl`) captured by temporarily re-registering
both policy objects **in memory only** (a scratchpad script, no repository
file touched) and running the identical real-match scenario this file used
before retirement. `*.jsonl` is repository-wide gitignored; a narrow
`.gitignore` negation (`!client/tests/fixtures/replay_status/*.jsonl`) was
added, mirroring the file's own "committed deliberately" precedent
pattern.

---

## I. Execution-vs-recognition boundary tests

New file: `test_v6_phase2b9_scope_a_retirement.py`, 19 cases, all passing
standalone. Covers, for all three retired identities symmetrically:

* **New execution rejected:** `resolve_ruleset_policy(retired_id)` raises
  `UnknownRulesetError` (parametrized, 3 cases) and the registry is
  confirmed disjoint from the retired-ID set (1 case).
* **Never silently aliased (T-12):** `normalize_ruleset_id(retired_id)`
  returns the ID unchanged and is never one of `bytefray-rules-2`/
  `bytefray-rules-4`; `resolve_ruleset_policy` still raises (3 cases).
* **Historical recognition preserved:** `normalize_ruleset_id` (3 cases); a
  hand-built replay header carrying the retired ID still resolves via
  `resolve_replay_ruleset` with `confidence="recorded"` (3 cases); a
  hand-built `ResultEnvelope` likewise via `resolve_result_ruleset` (3
  cases).
* **T-9 core-status membership, per identity** (not parametrized — the
  expected membership differs per identity): `bytefray-rules-2-alpha1` is
  vulnerable but not observable; `bytefray-rules-2-alpha11` and
  `bytefray-rules-3-alpha1` are both vulnerable and observable (3 cases).

Additional boundary coverage lives alongside the mixed-file fixes in §G
(placement fail-safe vs. dispatch fail-closed; VM dispatch rejection).

---

## J. Stable Ruleset-2 qualification

Run standalone, isolated basetemp, all green:

* `test_ruleset_v2_promotion_equivalence.py` — **12/12 passed** (new
  frozen-golden characterization, §C).
* `test_ruleset_v2.py` — **17/17 passed.**
* `test_ruleset_v2_runtime_compatibility.py` — **15/15 passed.**
* `test_v2_default_placement.py` — **28/28 passed.**
* `test_ruleset_policy.py` — **47/47 passed.**

Reference-agent and starter-agent coverage for `bytefray-rules-2`
(`test_agent_evaluation_v2_methodology.py`, `test_v2_alpha1_reference_agents.py`'s
successor coverage via the retained reference-agent test suite, Evaluation
API-v1 paths) passed in the full canonical run (§O) with **zero changes**
to those files beyond what §G lists. `bytefray-rules-2`'s fixed constants
(`CORE_SIZE=8`, `CORE_BEACON_BYTE=0xCE`), vulnerable/observable-core
mechanic, VM rejection, and canonical-identity behavior are all pinned,
unchanged, in `test_ruleset_v2.py`.

**Conclusion: retiring the two alphas did not modify stable Ruleset 2
semantics.** The golden characterization's own drift-sensitivity proof
(§C.4) is the direct evidence for this claim, not merely the absence of a
diff.

---

## K. Ruleset-4 control qualification

All of §E.3's protective files (`docs/research/v6/V6_PHASE2B8_LEGACY_RULESET_RETIREMENT_AUDIT.md`)
are confirmed **byte-for-byte unmodified** (`git diff --stat`: no output)
and passed in the final full-suite run:

| File | Cases |
| --- | ---: |
| `test_v4_stable_ruleset_equivalence.py` | 27 |
| `test_v4_runtime_default_ruleset.py` | 10 |
| `test_v4_historical_immutability.py` | 4 |
| `test_v4_alpha2_scheduler.py` | 18 |
| `test_v4_process_semantics.py` | 5 |
| `test_v4_trace_equivalence.py` | 2 |
| `test_v4_production_integration.py` | 24 |
| `test_v5_alpha1_phase_b_engine_hygiene.py` | 9 |
| `test_v5_starter_agents.py` | 54 |
| `test_v5_agent_parameters.py` | 124 |

(`test_v4_alpha2_placement.py` was modified, but only in the one
now-irrelevant-to-v4 row documented in §G; all 67 cases pass.)

`resolve_ruleset_policy("bytefray-rules-4")` still returns fields identical
to pre-phase: `seeded` / `round_robin` / `chunked` / chunk 2 / rotate
`True` / API `{2}` / python-only — unchanged, since nothing in this phase
touched `RULESET_V4`'s construction. **No Scope-A cleanup modified
Ruleset 4's gameplay policy.**

---

## L. Historical artifact qualification

Reproduced directly against the modified tree (not simulated), using both
this checkout's real, on-disk `runs/` corpus (53,458 `result.json` files,
matching the audit's own reported corpus size exactly) and the frozen
fixtures captured in §H:

```
registered rulesets: ['bytefray-rules-1', 'bytefray-rules-2', 'bytefray-rules-4',
                       'bytefray-rules-4-alpha1', 'bytefray-rules-4-alpha2']

=== bytefray-rules-3-alpha1 (real artifact) ===
  path: runs/research_v3_phase2/main/results/G_a4096_b2/group/lcamper_ltracker_ldefender/
        matches/0001-group-local_camper-local_core_tracker-local_core_defender-seed1-spread/result.json
  result: ruleset='bytefray-rules-3-alpha1' confidence='recorded' winner='A'
  replay: ruleset='bytefray-rules-3-alpha1' confidence='recorded' ticks=402
          cores=[('A', (8, False)), ('B', (8, False)), ('C', (0, True))]

=== bytefray-rules-2 (control, unaffected, real artifact) ===
  path: runs/evaluations/evaluation-v2_017737c34addb8bb268d2aef/matches/
        0001-group-claimer-hunter-wanderer-seed1-spread/result.json
  result: ruleset='bytefray-rules-2' confidence='recorded' winner='A'
  replay: ruleset='bytefray-rules-2' confidence='recorded' ticks=302
          cores=[('A', (6, False)), ('B', (3, False)), ('C', (3, False))]

=== frozen fixture: alpha1_attack_replay.jsonl ===
  ruleset='bytefray-rules-2-alpha1' confidence='recorded'
  cores=[('A', (0, True)), ('B', (8, False))]

=== frozen fixture: alpha11_no_attack_replay.jsonl ===
  ruleset='bytefray-rules-2-alpha11' confidence='recorded'
  cores=[('A', (8, False)), ('B', (8, False))]
```

Every row: correct result-envelope decode and attribution, full replay tick
reconstruction, correct per-entrant core-integrity/capture status — with
the registry narrowed to the current, post-retirement 5-identity state.
**No executable policy was needed for any of it**, and this checkout's real
corpus confirms the audit's own §N.2 proof still holds after the registry
change actually landed, not just before it.

---

## M. Defaults/product-surface verification

```
omitted API v2 python -> bytefray-rules-4
omitted API v1 python -> bytefray-rules-2
omitted VM             -> bytefray-rules-1
OMITTED_RULESET_CANDIDATES -> ('bytefray-rules-2', 'bytefray-rules-4', 'bytefray-rules-1')
DEFAULT_DESIGNER_RULESET_ID -> bytefray-rules-4
```

All unchanged from pre-phase. `cli.py`, `tournament_cli.py`,
`app/services/ruleset_options.py`, `evaluation_presets.py` — **zero diff**
(`git diff --stat`: no output for any of them). Since none of the three
retired identities was ever exposed on any CLI, Designer, or
evaluation-preset surface (confirmed by the audit's D.1 exposure matrix and
re-confirmed here by the absence of any diff to the files that would need
one), no surface edit was needed or made. Evaluation/Tournament current
behavior is unaffected — no diff to `tournament_service.py`,
`agent_evaluation.py`'s CLI entry points, or `evaluation_presets.py`.

---

## N. Collection reconciliation

| Checkpoint actually measured | Collected | Files | Note |
| --- | ---: | ---: | --- |
| Baseline (`--collect-only`, before any change) | 3,713 | 158 | Exact match to the charter's expected baseline |
| After A-1 (registry) / A-2 (evaluation allow-lists) / A-3 (research drivers), before touching any test file | **collection fails** — 2 `ImportError`s | — | `test_ruleset_policy.py`/`test_ruleset_v2.py` still imported the removed `RULESET_V2_ALPHA1`/`RULESET_V2_ALPHA11` objects; expected at this stage, resolved next |
| After the 11 whole-file removals **and** fixing the 2 import errors (`test_ruleset_policy.py` 49→47, `test_ruleset_v2.py` 16→17) | 3,427 | 147 | First point collection succeeds cleanly again; `158 − 11 = 147` files confirms exactly the 11 files removed and none other |
| After the remaining mixed-file fixes (`test_ruleset_v2_runtime_compatibility.py` 17→15; `test_v2_default_placement.py`, `test_v4_alpha2_placement.py`, `test_v4_interleaved_scheduler.py`, `client/tests/test_replay_status.py`, `test_ruleset_v2_promotion_equivalence.py` all unchanged in count) | 3,425 | 147 | Arithmetic (3,427 − 2); not separately re-collected as its own checkpoint |
| After adding `test_v6_phase2b9_scope_a_retirement.py` (+19) | **3,444** | **148** | Final — independently re-verified twice: once via the per-file collection reporter, once by summing a fresh `pytest --collect-only -q` |

**Exact arithmetic, baseline to final:** 3,713 − 285 (11 whole files,
summed individually in §G) − 2 (`test_ruleset_policy.py`) + 1
(`test_ruleset_v2.py`) − 2 (`test_ruleset_v2_runtime_compatibility.py`) +
19 (new boundary-test file) = **3,444.** Matches the measured final total
exactly — no unexplained deviation.

This falls outside the charter's own pre-implementation sanity range
(3,403–3,416), which is explained and expected: that range was computed
*before* the decision (§2) to convert rather than delete the 12-case
promotion-equivalence file, and before this implementation's own boundary
test file was written. The charter itself states this range is "a sanity
range, not a target" and that a deviation "is a finding to investigate,"
not a number to force — investigated above, fully attributable to two
deliberate, documented decisions (the conversion the charter itself
mandated, and the boundary tests the charter itself required in A-8), and
therefore closed.

---

## O. Canonical pytest/ruff/mypy qualification

Per this repository's standing integrity protocol: HEAD and SHA-256
digests of every phase-critical source file were recorded immediately
before, and re-verified identical immediately after, the final run.

**Full canonical suite** (`python -m pytest -q --basetemp=.pytest-tmp`, one
isolated invocation, no concurrent pytest process):

```
collected: 3,444
passed:    3,424
skipped:   20
failed:    0
errors:    0
```

One transient `PermissionError: Access is denied` (`os.replace` on a
Windows temp file) occurred on an **unrelated** test
(`test_agent_evaluation_group_analysis_integration.py::test_live_run_records_are_traceable_to_source_cells`,
group-analysis record traceability — no ruleset-identity involvement) in an
earlier, superseded full run. Reproduced alone (own isolated `--basetemp`):
passed. Reproduced with its entire containing file: 10/10 passed. Confirmed
transient (Windows file-handle contention during the large parallel-scale
run, not a real regression) per this repository's standing protocol, and
excluded from the counts above, which come from the subsequent, fully clean
final run.

**mypy:**

```
mypy engine/src/battle_engine  -> Success: no issues found in 107 source files
mypy client/src/battle_client  -> Success: no issues found in 16 source files
```

**ruff:**

```
ruff check .  -> All checks passed!
```

(Two mechanical `--fix` corrections were applied first — an import-sort
ordering issue and a `typing.Callable` → `collections.abc.Callable`
modernization, both in files this phase authored/rewrote, zero behavior
change — then the two affected files were re-run standalone, 31/31 passed,
before the final canonical run above.)

---

## P. Residue search

`git grep` for all three retired identity literals across every tracked
`.py`/`.md` file in the repository. Every hit classified:

**Historical (archived research/history) — untouched, correct:**
`docs/archive/v1/…v5/` (30+ files across the v2/v3/v4/v5 alpha/beta/rc
research record), `docs/research/v6/V6_PHASE0_BASELINE.md`,
`V6_PHASE1_REPOSITORY_DIET_AUDIT.md`,
`V6_PHASE2B5_REDCODE_PMARS_RETIREMENT_AUDIT.md`,
`V6_PHASE2B7_RULESET3_ALPHA1_DISPOSITION.md`,
`V6_PHASE2B8_LEGACY_RULESET_RETIREMENT_AUDIT.md` — prior phase reports,
immutable audit trail, never edited.

**Historical recognition (required reader/replay compatibility) —
retained verbatim:** `rules.py`, `result_model.py`, `replay.py`,
`replay_history/query.py` (a `RulesetFacet` docstring correctly documents
that the measured corpus contains these IDs), `app/services/replay_history_presentation.py`,
`client/src/battle_client/replay_status.py`, `agent_api.py`'s
`MatchContext.locality_reach`/`Observation.locus` field comments, and
every retained historical-recognition test in §H.

**Stable Ruleset-2 golden provenance (documentation/metadata explaining a
frozen characterization's source):** `test_ruleset_v2_promotion_equivalence.py`'s
module docstring and `EXPECTED` table comment (§C);
`docs/RULES_V2.md`'s "Ruleset identity and history" section (updated, see
"Documentation" below).

**Unexpected executable residue:** **none found.** Every production
call site of `resolve_ruleset_policy`/`_RULESET_POLICIES` was checked; none
resolves, executes, or is reachable for any of the three retired
identities. Every allow-list/membership table that named them was either
edited (registration, methodology, evaluation allow-list, core-placement
guard) or confirmed to be a historical-recognition table that must keep
their membership (`VULNERABLE_CORE_RULESET_IDS`/`OBSERVABLE_CORE_RULESET_IDS`).

**Comment corrections made for accuracy** (not executable, but were
actively misleading about current executability before this phase):
`docs/RULES_V2.md`'s VM-dispatch and "remain executable" paragraphs (see
"Documentation" below), `agent_api.py`'s `ActionKind` comment (§E), several
`ruleset_policy.py` inline comments (§D).

---

### Documentation

* `CHANGELOG.md` — new `### Removed — closed-research rulesets retired
  from execution` entry under `[Unreleased]`, mirroring the Redcode/pMARS
  entry's shape (per the charter's §R.2 recommendation).
* `docs/COMPATIBILITY.md` — new bullet in "Experimental/unsupported
  boundaries" plus a "Retired from execution / still recognised (V6 Phase
  2B.9)" table (per the charter's explicit instruction).
* `docs/RULES_V4.md` — one added paragraph naming `bytefray-rules-4` V6's
  single executable control and pointing at a future `bytefray-rules-6`
  for new gameplay; gameplay description unchanged.
* `docs/RULES_V2.md` — two paragraphs corrected (VM-dispatch carve-out,
  "Ruleset identity and history") that previously stated or implied the two
  alphas "remain executable" — now accurately past-tense, with the
  frozen-golden characterization's location named as where the promotion
  proof now lives.

Not touched: `README.md`, `AGENTS.md`, `SECURITY.md`, `docs/RULES.md`,
`docs/AGENT_AUTHORING.md`, `docs/AGENT_LAB.md`, `docs/AGENT_API_V2.md` —
none mentions any of the three retired identities (confirmed by `grep`);
`docs/FUTURE_PLANS.md`, `docs/ROADMAP.md` — already correctly framed in
past tense, no current-support claim to correct. No claim that Ruleset 1,
Ruleset 2, or either V4 alpha has been retired was made anywhere.

---

## Q. Quantified reduction

| Dimension | Before | After | Δ |
| --- | ---: | ---: | ---: |
| Executable ruleset identities | 8 | 5 | −3 |
| Identities with zero product exposure | 3 | 0 | −3 |
| Production LOC (6 touched files) | — | — | **−383 net** (175 ins / 558 del) |
| Research tools removed | — | — | 2 files, 1,495 LOC |
| Fixtures/data removed | — | — | 14 files, 1,669 LOC |
| Test files removed (whole) | — | — | 11 files, 5,414 LOC, 285 cases |
| Test files converted (not deleted) | — | — | 1 file (promotion-equivalence), 12 cases preserved |
| Test files pruned/fixed | — | — | 6 files |
| Test files added | — | — | 1 file, 173 LOC, 19 cases |
| Canonical tests collected | 3,713 | 3,444 | −269 |
| Documentation files edited | — | — | 4 (`CHANGELOG.md`, `COMPATIBILITY.md`, `RULES_V2.md`, `RULES_V4.md`) |
| Historical identities still recognized | — | — | All 3, fully (§H, §I, §L) |

**"8 executable registrations → 5"** — matches the charter's §23 expected
conceptual change exactly.

---

## R. Phase 3 / later-scope findings

Nothing new beyond what Phase 2B.8's own §X already recorded; this phase's
implementation confirms rather than adds to that list. Specifically
re-confirmed during implementation:

* The two-file identity-constant split (`rules.py` vs. `ruleset_policy.py`)
  made the "where does this ID constant live" question concrete during
  this phase's edits — no rule changed it, consistent with Phase 2B.8's
  recommendation that Phase 3 consider one.
* The `_RULESET_POLICIES` (execution) / `VULNERABLE_CORE_RULESET_IDS`
  /`OBSERVABLE_CORE_RULESET_IDS` (recognition) boundary was, in practice,
  the single most error-prone spot in this implementation — getting the
  `_CORE_PLACEMENT_GUARDED_RULESET_IDS` edit right (remove the membership,
  because the guard is reachable only after successful dispatch) while
  leaving the two core-status tables alone (because they are consulted
  independently of dispatch, by readers) required deliberate,
  file-by-file verification rather than a single mechanical rule. Phase
  2B.8's recommendation of an explicit, separate
  `historically_recognised_ids` table remains worth doing before the next
  retirement.
* Scope B's promotion-proof conversion (`test_v4_stable_ruleset_equivalence.py`,
  `test_v4_historical_immutability.py`) can now reuse this phase's
  frozen-golden pattern directly — the `_snapshot`/`_snapshot_digest`/
  `EXPECTED`-table shape here is a second working instance of the pattern
  `test_ruleset_v1_equivalence.py` established, making it a confirmed,
  twice-used template rather than a one-off.

The four Ruleset-1 fallback problems (T-1/T-2/T-3/T-11) and Scope
B/C themselves remain exactly as Phase 2B.8 left them — recorded there,
not touched here, per the charter's explicit boundary.

---

## S. Unexpected findings

None that changed this phase's plan. Two items worth recording as
process notes:

1. **`core_placement_mode`'s fail-*safe* (not fail-closed) design** (T-4)
   was directly observed to still apply to the newly-retired identities
   exactly as the audit predicted — `resolve_direct_match_starts` returns
   `(0, 0)` for a retired ID rather than raising, and only real dispatch
   (`resolve_ruleset_policy` inside `NativeMatchService.run`) actually
   rejects it. This was not a defect to fix (the charter explicitly scoped
   T-4 as "add a test pinning [it]," not "repair it," and repairing it
   would be exactly the kind of Ruleset-1-fallback-family change the
   charter's §12 puts out of scope) — it was a design fact that made two
   existing tests' *reason* wrong even though their *assertion* was almost
   right, requiring careful reading rather than a mechanical find-replace.
2. **The "keep the parameter, make it permanently inert" pattern** (used
   for `PythonEntrantController.locality_reach`,
   `MatchRequest.locality_reach`, `EvaluationRequest.locality_reach`,
   `_resolve_locality_reach`, `resolved_locality_reach`) was a deliberate
   choice to keep this phase's edit surface inside the audit's own
   measured file list, rather than cascading into `agent_worker.py`,
   `evaluation_worker.py`, and `agent_test.py`'s wire/request plumbing,
   which the audit's Q.2 LOC estimates did not include and which carry
   materially higher risk (subprocess IPC boundaries) for materially
   lower benefit (dead code that can never execute either way). Recorded
   here so a future phase doesn't rediscover the same question from
   scratch.

---

## T. Final repository state

* Working tree: **not committed**, per the charter's §26 — left for
  review. `git status --short` shows exactly the files this report
  describes (§D–§I, and the "Documentation" list under §P), nothing else.
* `main`: untouched (`82549f9c…`, identical to `origin/main` throughout).
* `v6-research`: HEAD unchanged at `b55b8ea49019bd3ca5f1710b79fd4dfe5b6be24c`
  (this phase's work is entirely uncommitted working-tree state, as
  instructed); still 0 ahead / 0 behind `origin/v6-research` for the
  commits that exist.
* Canonical suite: 3,444 collected / 3,424 passed / 20 skipped / 0 failed
  / 0 errors. `mypy` (engine + client) clean. `ruff` clean.
* No retired identity is executable. All three remain fully readable,
  attributable, indexable, filterable, and replayable, proven against both
  real on-disk historical artifacts and frozen fixtures, with permanent
  regression coverage for both sides of the contract.
