# Bytefray V6 — Phase 2B.10: Scope B V4 Alpha Retirement

**Phase type:** Implementation. Retires `bytefray-rules-4-alpha1` and
`bytefray-rules-4-alpha2` from executable registration, per Phase 2B.8's
audit disposition
(`docs/research/v6/V6_PHASE2B8_LEGACY_RULESET_RETIREMENT_AUDIT.md`),
implementing exactly Scope B of that audit's three-scope plan. Scope A was
completed by Phase 2B.9; Scope C (Agent API v1/VM retirement) remains
explicitly out of scope and untouched.

**Governing principle, restated from the charter:** retire the prerelease
engines without weakening the proof of the stable control they produced.

---

## A. Baseline

Established before any change, per the charter's §2:

| Check | Result |
| --- | --- |
| Branch | `v6-research` — confirmed |
| HEAD SHA | `8244e6b588397206d482ddaf2245201f5f09d80d` |
| Phase 2B.9 | Committed in HEAD (two commits: `8244e6b`/`f2339c0`, "Bytefray V6 Phase 2B.9 — Retire Closed Research Rulesets") |
| Working tree at phase start | Clean (`git status --short` empty) |
| Divergence from `origin/v6-research` | 0 ahead, 0 behind |
| `main` | untouched throughout (not referenced by any command this phase ran) |
| Canonical tests collected | **3,444** across 148 files — exact match to the charter's expected post-2B.9 baseline |

---

## B. Scope implemented

**Scope B only**, per the charter. Retired from executable registration:

* `bytefray-rules-4-alpha1`
* `bytefray-rules-4-alpha2`

Left untouched and fully executable: `bytefray-rules-1`, `bytefray-rules-2`,
`bytefray-rules-4`. `bytefray-rules-4` remains the frozen V6 research
control. Scope C (Agent API v1/VM retirement) was explicitly left alone,
per the charter's §23 boundary.

---

## C. Alpha2 promotion-proof conversion

Per the charter's §3 (the phase's single most important requirement),
`bytefray-rules-4-alpha2`'s executable registration could not be removed
until its promotion-equivalence proof
(`engine/tests/test_v4_stable_ruleset_equivalence.py`, 27 collected cases,
described in its own pre-conversion module docstring as
**release-blocking**) was converted from a live two-ruleset comparison into
a frozen-golden characterization. Done **before** any registry edit, in
this order:

1. **Original corpus re-confirmed passing.** The unmodified,
   pre-conversion test file was run standalone (isolated `--basetemp`):
   **31/31 passed** (27 equivalence cases + 4
   `test_v4_historical_immutability.py` cases run together), confirming
   the live alpha2-vs-stable equivalence still held for every one of the
   23 ruleset-dependent scenario cases before any conversion began.
2. **Golden derived from the confirmed-passing baseline.** A scratchpad
   capture script (not committed) reused this file's exact
   pre-conversion scenario corpus and helper functions
   (`_run_under_ruleset`, `_canonical_replay_records`,
   `_assert_gameplay_equivalent_and_identity_differs`), ran each of the 22
   regular scenarios plus the tick-limit scenario under
   `bytefray-rules-4-alpha2` **and** `bytefray-rules-4` while both were
   still fully registered, re-asserted the file's own live-equivalence
   assertions for every one, then derived a SHA-256 digest of the
   alpha2-side canonical (nulled-identity) snapshot — the complete
   replay header, full tick sequence, and terminal result, exactly the
   shape `dataclasses.asdict` produces — plus summary fields
   (`ticks_run`, `termination_reason`, `winner`) for diagnosability.
3. **New characterization confirmed passing.** The rewritten test
   file — same scenario corpus and helper functions, now running only
   under `bytefray-rules-4` and comparing against the frozen `EXPECTED`
   table — was run standalone: **27/27 passed** (23 scenario cases + 4
   starter-source-validity regression cases, unaffected by the
   conversion).
4. **Drift-sensitivity demonstrated.** `battle_engine.process_runtime`'s
   `disruption_duration` was temporarily changed from `1` to `2` (a
   real gameplay-behavior mutation — how long a disrupted process stays
   disrupted — reverted immediately after), and the golden test file was
   re-run: **22 of 23 scenario cases failed** on digest mismatch (the one
   surviving case, the tick-limit scenario between two short-reach
   defenders, never triggers disruption, so it is correctly insensitive
   to this specific mutation — the 4 bootstrap cases, which touch no
   ruleset execution at all, were likewise unaffected). This confirms the
   characterization actually detects behavioral drift rather than passing
   vacuously. The revert was verified with `git diff --stat` (empty for
   `process_runtime.py`) and a clean re-run (31/31 passed).

The differentiation from a vacuous pass is structural, not just the
mutation test above: each scenario's digest covers the complete
nulled-identity header/tick-sequence/result, and the raw (non-nulled)
header assertion (`raw_header.ruleset_id == BYTEFRAY_RULESET_V4_ID`) is a
real, live assertion against the control's own execution — the frozen
side of the comparison no longer needs a "must differ" check, since alpha2
can no longer execute at all to produce a live value that could
accidentally match.

**Provenance recorded in the file itself:** the module docstring names the
exact commit the golden values were captured at
(`8244e6b588397206d482ddaf2245201f5f09d80d`, the pre-Scope-B HEAD),
states the reproduction method (check out that commit's version of the
file, which still exercises alpha2 directly, and rerun it), and restates
the versioning policy copied from the Phase 2B.9/`test_ruleset_v1_equivalence.py`
precedent: a legitimate Ruleset 4 gameplay/Agent API/RNG/schema change must
version `EXPECTED` deliberately, never refresh it in place to make a
regression pass.

Collected case count for this file: **27 → 27 (unchanged)** — converted,
not deleted, consistent with the charter's explicit instruction.

### C.1 Historical immutability conversion

`engine/tests/test_v4_historical_immutability.py` (4 cases, also
identified by the audit as depending on alpha2's/alpha1's executability)
was converted alongside the equivalence file, following the same
frozen-golden discipline but adapted to two genuinely different concerns
it protects (see the file's own module docstring for the full reasoning):

1. **Canonical-identity pinning** (`test_alpha1_and_alpha2_canonical_ids_are_pinned`,
   pre-conversion) — converted to load two frozen fixture replays
   (`engine/tests/fixtures/v4_historical_immutability/alpha1_pinned_seed5_replay.jsonl`,
   `alpha2_pinned_seed5_replay.jsonl`, captured pre-retirement from the
   exact pre-conversion scenario, committed via a `.gitignore` negation
   mirroring Phase 2B.9's `client/tests/fixtures/replay_status/` precedent)
   and assert their headers still carry the literal pinned
   `match_id`/`result_id` values this suite pinned since before the
   stable identity existed. Split into two permanent tests: one for the
   pinned identity check, one (`test_frozen_interleave_fixtures_confirm_alpha1_was_immune_to_control_interleaving`)
   preserving the frozen record of the last live confirmation that
   running the control between two alpha1 runs left the second
   byte-identical to the first.
2. **Cross-execution state isolation for the live control**
   (`test_stable_v4_execution_does_not_mutate_state_a_subsequent_alpha_match_reads`,
   pre-conversion) — necessarily generalized, since alpha1 is no longer a
   second live process-Ruleset to interleave with (after this phase,
   `PROCESS_RULESET_IDS` has exactly one member). Reformulated as
   `test_stable_v4_execution_is_unaffected_by_an_interceding_execution_under_a_different_ruleset`:
   runs the control, then an interceding match under the still-executable
   `bytefray-rules-2` (a different runtime controller entirely —
   `PythonEntrantController`, not `ProcessMatchController`), then the
   control again with identical inputs, asserting the second run
   reproduces the first exactly. This is an honestly narrower guarantee
   in one respect (no longer specifically proving isolation between two
   *process*-Ruleset executions, since only one exists) — recorded
   explicitly in the file's module docstring rather than silently
   presented as equivalent, with the structural fact that
   `process_runtime.py` contains zero Ruleset-identity branching cited as
   the strongest remaining evidence for the narrower claim.

The 2 starter-source-validity regression tests in this file, which never
touch ruleset execution, were left untouched.

Net case count for this file: **4 → 5** (+1 — three permanent tests now
cover what two did before, since the canonical-identity concern split into
a pinned-fixture check and a frozen-interleave check).

---

## D. Registry/policy retirement

`engine/src/battle_engine/ruleset_policy.py`:

* Removed the `RULESET_V4_ALPHA1` and `RULESET_V4_ALPHA2` policy objects,
  their `_RULESET_POLICIES` entries, and their `PROCESS_RULESET_IDS`
  entries (`PROCESS_RULESET_IDS` now has exactly one member,
  `bytefray-rules-4`).
* Removed their two `__all__` entries (the policy-object names only).
* **Kept** both `BYTEFRAY_RULESET_V4_ALPHA1_ID`/`BYTEFRAY_RULESET_V4_ALPHA2_ID`
  string constants, still exported in `__all__`, for historical
  recognition.
* Updated the module's own prose (the retirement comment above the removed
  objects, the `_RULESET_POLICIES`/`PROCESS_RULESET_IDS` docstrings, and
  `RULESET_V4`'s own promotion comment) to state the retirement and point
  at its replacement evidence rather than describing two now-nonexistent
  live objects.

`engine/src/battle_engine/match_service.py`:

* Removed `bytefray-rules-4-alpha1`/`bytefray-rules-4-alpha2` from
  `_CORE_PLACEMENT_GUARDED_RULESET_IDS` — a pre-execution overlap guard
  for a match *about to run*, confirmed to have zero historical-reader
  consumers (unlike the two core-status tables in `python_runtime.py`,
  §H), so retiring both alphas' executable registration made their
  membership here dead. `bytefray-rules-2`/`bytefray-rules-4` remain.

`app/services/designer_workflows.py`:

* Narrowed `DESIGNER_AUTO_TRACE_RULESET_IDS` to `{bytefray-rules-4}`.
  Confirmed (by tracing its only consumer, `designer_trace_path`, to its
  only two call sites in `app/agent_designer.py`, both immediately before
  launching a *new* match) that this table is execution-only with no
  historical-reader dependency, unlike the methodology tables below.

`engine/src/battle_engine/agent_evaluation.py`:

* Removed `bytefray-rules-4-alpha1`/`bytefray-rules-4-alpha2` from the
  low-level `EvaluationRequest` validation allow-list (raises
  `EvaluationConfigurationError` for either now) and from the CLI's
  `--ruleset` choices (`argparse` `choices=`).
* **Deliberately left `_V2_METHODOLOGY_RULESET_IDS`/
  `_V4_METHODOLOGY_RULESET_IDS` untouched** — see §D.1, a documented
  deviation from the charter's own illustrative table list, with evidence.

**Behavioral verification** (direct execution against the modified tree):

```
registered: ['bytefray-rules-1', 'bytefray-rules-2', 'bytefray-rules-4']
PROCESS_RULESET_IDS: ['bytefray-rules-4']
bytefray-rules-4-alpha1   -> UnknownRulesetError OK
bytefray-rules-4-alpha2   -> UnknownRulesetError OK
bytefray-rules-1          -> resolves OK
bytefray-rules-2          -> resolves OK
bytefray-rules-4          -> resolves OK
ID constants still present: bytefray-rules-4-alpha1 bytefray-rules-4-alpha2
_CORE_PLACEMENT_GUARDED_RULESET_IDS: ['bytefray-rules-2', 'bytefray-rules-4']
VULNERABLE_CORE contains alpha1: True
OBSERVABLE_CORE contains alpha1: True
```

No retired ID maps to `bytefray-rules-2` or `bytefray-rules-4` anywhere
(T-12) — confirmed both structurally (no such mapping was added) and by
test (`test_v6_phase2b10_scope_b_v4_alpha_retirement.py`, §M).

### D.1 A documented deviation from the charter's illustrative list: methodology tables were NOT touched

The charter's §6 lists `_V2_METHODOLOGY_RULESET_IDS` among the tables to
remove Alpha1/Alpha2 from, "including as applicable." Tracing both
methodology tables' actual consumers before editing found this is **not**
applicable — both are dual-use, exactly the T-9 conflation pattern the
audit warned is "the single highest-risk item in every scope":

* `_V2_METHODOLOGY_RULESET_IDS = {bytefray-rules-2, bytefray-rules-4-alpha1}`
  (alpha1 was **always** a member here — it uses v2-style fixed placement,
  not the v4-seeded methodology — this membership predates and is
  unrelated to this phase).
* `_V4_METHODOLOGY_RULESET_IDS = {bytefray-rules-4-alpha2, bytefray-rules-4}`.
* `is_ruleset_v2_methodology`/`is_ruleset_v4_methodology`, which read
  these tables, are called from
  `engine/src/battle_engine/evaluation_history/verification.py:475` and
  `evaluation_history/cli.py:140` — both **historical artifact
  verification/comparison** call sites, reading a **persisted**
  `rules_compatibility_id` from a stored `EvaluationSummary`
  (`FieldConfidence.RECORDED` guarded), not a live request.

Removing alpha1/alpha2 from these tables would have broken historical
evaluation-artifact verification (`verify_summary`'s placement
reconstruction check) for every stored alpha1/alpha2 evaluation, exactly
the historical-recognition regression T-9 already named for the core-status
tables. This is recorded as a deliberate, evidence-based deviation from the
charter's own example list — per this repository's standing rule that
current code and observed behavior outrank a task's illustrative list when
they conflict — and is directly protected by
`test_is_ruleset_v4_methodology_is_exactly_alpha2_and_stable_v4`
(`engine/tests/test_agent_evaluation_v4.py`, unmodified by this phase,
still passing) and by `test_evaluation_history_comparison.py`'s existing
hand-built-fixture coverage for both methodologies (also unmodified).

By contrast, `DESIGNER_AUTO_TRACE_RULESET_IDS` (§D) *was* narrowed, because
tracing its one consumer found no historical-reader dependency at all —
the two tables are structurally identical (both `frozenset[str]` gates
keyed on Ruleset ID) but semantically opposite, and only direct
call-site tracing distinguishes them.

---

## E. Product-surface changes

`app/services/ruleset_options.py`:

* Removed the `RULESET_V4_ALPHA1_OPTION`/`RULESET_V4_ALPHA2_OPTION`
  `DesignerRulesetOption` objects entirely.
* `EVALUATION_RULESET_OPTIONS`: `(v2, v4, v1)` — was `(v2, v4, alpha2,
  alpha1, v1)`.
* `DESIGNER_RULESET_OPTIONS` (Advanced/Development): `(v2, v4, v1)` — was
  `(v2, v4, alpha2, alpha1, v1)`.
* `SIMPLE_RULESET_OPTIONS` unchanged (`(v2, v4)` — never offered either
  alpha).
* `RULESET_DESCRIPTION`/`VM_RULESET_EXPLANATION` prose strings: removed
  the sentences naming alpha1/alpha2 as currently-offered options.

Four CLI `--ruleset` `choices=` lists (`cli.py`, `tournament_cli.py`,
`agent_test.py`, `agent_evaluation.py`) all narrowed identically from
`{v1, v2, alpha1, alpha2, v4}` to `{v1, v2, v4}`; their unused
`BYTEFRAY_RULESET_V4_ALPHA1_ID`/`BYTEFRAY_RULESET_V4_ALPHA2_ID` imports
were removed alongside.

**Behavioral verification:**

```
bytefray run --help            -> choices {bytefray-rules-1,bytefray-rules-2,bytefray-rules-4}
bytefray tournament --help     -> choices {bytefray-rules-1,bytefray-rules-2,bytefray-rules-4}
bytefray agents test --help    -> choices {bytefray-rules-1,bytefray-rules-2,bytefray-rules-4}
bytefray agents evaluate --help -> choices {bytefray-rules-1,bytefray-rules-2,bytefray-rules-4}
Designer Simple offered:   {bytefray-rules-2, bytefray-rules-4}
Designer Advanced offered: {bytefray-rules-1, bytefray-rules-2, bytefray-rules-4}
Designer Development (API v2 agent) offered: {bytefray-rules-4}
Evaluation (API v2 candidate) offered:       {bytefray-rules-4}
```

(See §L for the full 82-case GUI-marked test run confirming these values
live, against real Qt widgets under `QT_QPA_PLATFORM=offscreen`.)

---

## F. Spectator-test re-pointing

Per the charter's §8, the exact audit mapping was used, not a blind
string replacement, and each file's usage was individually verified
before re-pointing (see §F.1 for the one case that was *not* safe to
re-point). Re-pointed from `bytefray-rules-4-alpha1`/`RULESET_V4_ALPHA1`
(and, in one file, `RULESET_V4_ALPHA2`) to `bytefray-rules-4`/`RULESET_V4`,
confirmed by grep to carry **no** assertions on `core_placement`,
`process_selection`, or alpha-specific placement geometry (i.e., every
usage was "some process ruleset to run a match under" for spectator/CLI
subsystem testing, never alpha-semantic testing):

| File | Cases | Change |
| --- | ---: | --- |
| `test_v4_spectator_derivation.py` | 36 | Re-pointed (6 call sites) |
| `test_v4_spectator_perspective.py` | 23 | Re-pointed (import + 2 call sites, including the ALPHA2 one) |
| `test_v4_spectator_fight_night.py` | 19 | Re-pointed |
| `test_v4_spectator_director.py` | 13 | Re-pointed |
| `test_v4_spectator_multi_entrant.py` | 7 | Re-pointed |
| `client/tests/test_perspective.py` | 12 | Re-pointed |
| `client/tests/test_fight_night.py` | 22 | Re-pointed (1 call site; a second literal-string `ruleset_label` usage in a pure text-layout test was confirmed registry-independent and left alone) |
| `client/tests/test_director.py` | 9 | Re-pointed |
| `test_v4_trace_equivalence.py` | 2 | Re-pointed |
| `test_designer_workflows.py` | 18 | Re-pointed 2 live-match tests; converted the trace-path parametrize tests (§G) |

All case counts unchanged by re-pointing alone (content rewritten, test
count preserved), consistent with the charter's "do not blindly replace
every string occurrence" instruction being followed rather than skipped.

### F.1 `client/tests/test_perspective_card_knowledge.py` — the one file that could NOT be blindly re-pointed

`test_real_match_hidden_opponent_core_loss_never_reaches_a_perspective_card`
uses a real match (via a hand-crafted `_kill()` executioner/sleeper
fixture) to prove a hidden opponent *core* loss never reaches a Perspective
card. Re-pointing its `ruleset_id` to `bytefray-rules-4` was tried first
and produces a test that **fails on its own precondition guard** — not a
flaky failure, a structural one: `bytefray-rules-4` is not a member of
`VULNERABLE_CORE_RULESET_IDS`/`OBSERVABLE_CORE_RULESET_IDS` (§D.1's sibling
finding — this is pre-existing, deliberate product behavior, unrelated to
this phase), so `client/src/battle_client/replay_status.py`'s
`_core_status` returns `None` for *any* stable-v4 match, unconditionally.
A search across 400+ seed/arena/geometry combinations under stable v4,
plus a redesigned agent write-cadence, confirmed this is not a rare seed
but a structural impossibility: **among Agent-API-v2/process Rulesets,
only `bytefray-rules-4-alpha1` was ever a member of either core-status
table.** Retiring it does not just remove one identity choice for this
fixture — it removes the *only* Ruleset that could ever produce this
regression's precondition live.

Per the charter's §10 guidance ("prefer converting it to a frozen
persisted-artifact... characterization" over discarding real coverage),
this test now loads a real `bytefray-rules-4-alpha1` replay+trace pair
captured before retirement
(`client/tests/fixtures/perspective_card_knowledge/`, committed via a
`.gitignore` negation) instead of running a live match. Every assertion
the test makes is otherwise unchanged — real reader-layer evidence
(`get_entrant_statuses`, `PerspectiveManager`, `PygameRenderer`) driven
from a real recorded match, not a hand-built fixture; only the execution
step moved before retirement. File case count unchanged: **12 → 12.**

This is recorded as the single most important correctness finding of the
spectator re-pointing pass: a naive "swap the ruleset constant" edit here
would have produced a test that either failed loudly (caught) or, with a
weaker assertion style, could have silently stopped testing anything
about hidden core loss.

---

## G. Alpha-specific tests/tools removed

### G.1 Whole-file removal

`engine/tests/test_v4_alpha2_integration.py` (8 cases) — removed, per the
audit's own explicit recommendation ("REMOVE whole file — the only genuine
alpha-defining file"). Every one of its 8 tests directly compared live
alpha1 vs. live alpha2 execution (canonical-id distinctness, seeded
placement reproducibility, schema pinning, process-runtime dispatch,
determinism, multi-process gameplay divergence, and the "alpha1 firewall"
cross-contamination check) — none can execute after retirement. The
essential evidence this file protected is preserved elsewhere: alpha2≡stable
equivalence lives on as the frozen-golden characterization (§C); alpha1's
frozen identity/isolation properties live on as the fixture-backed tests in
`test_v4_historical_immutability.py` (§C.1); the two alphas' distinct
policy field values are documented in `ruleset_policy.py`'s own retirement
comment and reconstructed locally in `test_v4_runtime_default_ruleset.py`/
`test_v4_alpha2_scheduler.py` (§I).

### G.2 Research tools removed

| Path | Kind | LOC |
| --- | --- | ---: |
| `tools/v4_alpha2_ecology_study.py` | research driver | 935 |
| `tools/v4_r0c_rotation_qualification.py` | research driver | 231 |
| `tools/v4_scheduler_experiment.py` | research driver | 301 |
| `tools/v4_scheduler_grain_sweep.py` | research driver | 380 |
| **Total** | | **1,847** |

Zero remaining importers confirmed (`git grep` for each module name,
repo-wide, before deletion — only the ecology-study file's own self-match
appeared).

### G.3 Tests removed (whole-file) or with entire cases removed

| File | Change |
| --- | --- |
| `test_v4_alpha2_integration.py` | Removed (8 cases, §G.1) |
| `test_agent_evaluation_v4.py` | Removed `test_explicit_alpha2_ruleset_uses_the_stable_v4_methodology_under_its_own_identity` and `test_explicit_alpha1_ruleset_keeps_its_historical_fixed_placement_methodology` (their claims are now false — explicit alpha1/alpha2 selection no longer works); added a 2-case negative-CLI parametrize test in their place (net 0 for this swap). Removed `test_rendered_summary_reports_v4_seeded_placements_for_alpha2` (now redundant with the stable-v4 sibling test, since alpha2 cannot run to prove a second identity independently); no replacement (net −1). File total: **31 → 30.** |
| `test_ruleset_policy.py` | Removed `test_v4_alphas_remain_explicitly_selectable_after_stable_v4_takes_the_default` (its claim is now the opposite of what this phase establishes); replaced with `test_v4_alphas_are_no_longer_selectable_after_v6_phase_2b10_retirement` (net 0). File total: **47 → 47.** |
| `test_designer_ruleset_options.py` | Removed `test_the_three_v4_options_are_distinguishable_to_a_reader` (−1; its premise, three distinguishable v4 labels, no longer holds — only one v4 option exists). The anti-drift guard test parametrized over `DESIGNER_RULESET_OPTIONS` (`test_designer_compatibility_always_agrees_with_engine_policy`) automatically shrank from 6 metadata × 5 options = 30 cases to 6 × 3 = 18 (−12) as the underlying options tuple narrowed (§E) — not a separate edit, a consequence of it. File total: **48 → 35.** |

---

## H. Historical-recognition coverage retained

Verbatim, unmodified (confirmed by `git diff --stat` showing no diff for
`python_runtime.py`):

* `BYTEFRAY_RULESET_V4_ALPHA1_ID`, `BYTEFRAY_RULESET_V4_ALPHA2_ID`
  (`rules.py` — untouched, string constants only)
* `resolve_result_ruleset` / `resolve_replay_ruleset`, including their
  `"recovered"` branches (`result_model.py`, `replay.py` — untouched)
* `VULNERABLE_CORE_RULESET_IDS` / `OBSERVABLE_CORE_RULESET_IDS`
  **membership** for `bytefray-rules-4-alpha1` — the single most
  consequential T-9 case in this phase, since without it
  `client/tests/test_perspective_card_knowledge.py`'s real-match
  regression would have had no live Ruleset able to reproduce its
  precondition at all (§F.1) — `python_runtime.py` is byte-for-byte
  unmodified.
* `_V2_METHODOLOGY_RULESET_IDS` / `_V4_METHODOLOGY_RULESET_IDS`
  **membership** for both alphas (§D.1) — a deliberate deviation from the
  charter's illustrative removal list, evidence-based.
* `has_vulnerable_core`, `has_observable_core`, `is_ruleset_v2_methodology`,
  `is_ruleset_v4_methodology` (still callable, still correct for both
  retired IDs — verified in §M)
* `_readable_ruleset` / `ruleset_label`
  (`app/services/replay_history_presentation.py`, untouched — shape-derived,
  no table, no registry coupling)

---

## I. Alpha1 historical characterization preserved without live execution

Because alpha1 genuinely differed from the control on two gameplay
semantics (`core_placement`, `process_selection`), three permanent test
suites that characterize the *shared implementation's* response to those
field values — not registry dispatch — needed the named
`RULESET_V4_ALPHA1`/`RULESET_V4_ALPHA2` objects, which no longer exist as
importable names after §D. All three construct/pass a `RulesetPolicy`
object **directly** to `ProcessMatchController`, never resolving one by ID
string, so their tests remain 100% functionally independent of the
executable registry — only the import needed fixing:

* `test_v4_runtime_default_ruleset.py` (10 cases) — reconstructs
  `_FROZEN_ALPHA1_POLICY`/`_FROZEN_ALPHA2_POLICY` locally, with field
  values traceable to `ruleset_policy.py`'s own retirement comment.
* `test_v4_alpha2_scheduler.py` (18 cases) — reconstructs the same two
  objects under their original names (`RULESET_V4_ALPHA1`/
  `RULESET_V4_ALPHA2`), so no other line in the file needed changing.
* `test_v4_process_semantics.py` (5 cases) — reconstructs
  `RULESET_V4_ALPHA1` only (the only one this file used).

All three files' case counts are unchanged (10, 18, 5) and all pass
unmodified in substance — this is a preservation, not a reduction, of
Ruleset 4 control-protecting coverage (all three are named in the audit's
§E.3 "must survive every cleanup" list).

`test_v4_alpha2_placement.py` (67 cases, also on that list) needed a
different fix: it calls `placement.core_placement_mode`/
`resolve_direct_match_starts` **by ID string**, which — like
`resolve_v4_seed_geometry` (§K) — fails *safe* to the masked `"zero"`
default for a retired ID (T-4), rather than raising. Two rows in
`test_each_ruleset_keeps_its_own_placement_mode`'s parametrize table
(`(alpha1_id, "seat_spread")`, `(alpha2_id, "seeded")`) were updated to
`"zero"`, matching the exact precedent Phase 2B.9 already set for
`bytefray-rules-3-alpha1` in this same file. Two more tests
(`test_alpha1_placement_is_the_historical_opposite_pair`,
`test_alpha2_requires_a_seed_rather_than_inventing_one`,
`test_explicit_starts_survive_alpha2_placement_untouched`) asserted the
*real* historical placement value via live dispatch — renamed/re-pointed
to pin the masked fallback explicitly (alpha1's case) or re-point to the
stable control, which shares alpha2's exact seeded-placement gameplay
(alpha2's two cases). File case count unchanged: **67 → 67.**

---

## J. Negative execution tests (T-12, Section 15)

New dedicated file `test_v6_phase2b10_scope_b_v4_alpha_retirement.py` (16
cases), mirroring Phase 2B.9's `test_v6_phase2b9_scope_a_retirement.py`
pattern:

* **New execution rejected:** `resolve_ruleset_policy(retired_id)` raises
  `UnknownRulesetError` (parametrized, 2 cases); the registry is confirmed
  disjoint from both retired IDs and from `PROCESS_RULESET_IDS` (1 case).
* **`NativeMatchService.run` rejects before any artifact write** (2
  cases, parametrized) — confirmed no `replay.jsonl` parent directory is
  created for a doomed request.
* **Never silently aliased (T-12):** `normalize_ruleset_id(retired_id)`
  returns the ID unchanged and is never one of `bytefray-rules-2`/
  `bytefray-rules-4`; `resolve_ruleset_policy` still raises (2 cases).
* **Historical recognition preserved:** `normalize_ruleset_id` (2 cases); a
  hand-built replay header carrying either retired ID still resolves via
  `resolve_replay_ruleset` with `confidence="recorded"` (2 cases); a
  hand-built `ResultEnvelope` likewise via `resolve_result_ruleset` (2
  cases).
* **T-9 core-status membership, asymmetric by design** (3 cases, not
  parametrized — alpha1 and alpha2 have genuinely different membership):
  alpha1 is both vulnerable and observable; alpha2 is neither (this was
  always true, unrelated to retirement); the stable control is neither
  either (confirming Scope B changed no gameplay-observable behavior for
  the control itself).

Additional negative-execution coverage lives alongside the mixed-file
fixes elsewhere: `test_ruleset_agent_compatibility.py` gained
`test_agent_supported_by_ruleset_fails_closed_for_retired_alpha_identities`
(6 cases) and
`test_native_match_service_rejects_retired_alpha_identity_before_agent_compatibility`
(2 cases); `test_agent_evaluation_v4.py` gained
`test_explicit_retired_v4_alpha_ruleset_is_rejected_by_the_evaluation_cli`
(2 cases); `test_agent_test.py`'s and `test_cli_characterization.py`'s CLI
help/explicit-selection tests were converted to prove rejection (§E).

---

## K. A T-4-class trap found beyond the audit's own list: `resolve_v4_seed_geometry`

`test_agent_evaluation_v4.py::test_pinned_seed_vectors_match_the_research_report`
called `resolve_v4_seed_geometry(BYTEFRAY_RULESET_V4_ALPHA2_ID, 512, 3)`,
asserting the exact pinned vector `(495, 387)` the research report cites.
This was initially assumed pure-function-safe (no live dispatch) and left
unchanged — a full `pytest` run proved that assumption wrong:
`resolve_v4_seed_geometry` resolves its Ruleset's `core_placement` mode
through the executable registry exactly like `placement.core_placement_mode`
(T-4) and fails *safe* to the masked default for a retired ID, returning
`(0, 0)` instead of the real seeded vector — silently wrong, not merely
inert. Re-pointed to `bytefray-rules-4`, which reproduces the identical
pinned vector by construction (placement's domain-separation payload is a
fixed constant, not the ruleset id — audit Sec E.1/J), with the T-4
mechanism documented directly in the test's own docstring. This is recorded
here specifically because it was **not** in the audit's or charter's
enumerated trap list, and was only caught by actually running the test
rather than reasoning about the function's signature — direct evidence for
this repository's standing rule to verify a hypothesis by execution rather
than by inspection alone.

---

## L. Product ruleset surfaces — GUI qualification

The four root-`tests/` GUI files (`@pytest.mark.gui`, outside the
canonical `testpaths`, exercised by the dedicated display-backed workflow)
were updated in lockstep with §E's production changes and re-run directly
(`QT_QPA_PLATFORM=offscreen`, PySide6 available in this environment):

```
tests/test_v5_alpha1_phase_e_designer_ux.py
tests/test_agent_designer_lifecycle.py
tests/test_agent_combo_runtime_labels.py
tests/test_designer_ruleset_compatibility.py
-> 82 passed
```

Changes: `test_the_designer_never_offers_a_rejected_research_ruleset`'s
expected offered-set narrowed (no alpha1/alpha2);
`test_designer_run_requests_trace_only_for_v4_rulesets`'s alpha1/alpha2
parametrize rows removed (neither remains selectable to launch at all);
`ALL_V4_IDENTITIES` narrowed to `{bytefray-rules-4}` in
`test_designer_ruleset_compatibility.py`, cascading correctly through
Development's and Evaluation's offered-set assertions; stale
"alpha2/alpha1 stay selectable" comments corrected.

---

## M. Historical artifact qualification

Reproduced directly against the modified tree (not simulated), using this
checkout's real, on-disk `runs/` corpus.

### M.1 Real-artifact decode, attribution, and replay reconstruction

```
=== alpha1 artifact: runs\_designer\20260903-005148-33a277b7\result.json ===
  result ruleset=bytefray-rules-4-alpha1 confidence=recorded winner=B
  replay ruleset=bytefray-rules-4-alpha1 confidence=recorded
  entrant A: alive=True intact=8/8 captured=False
  entrant B: alive=True intact=8/8 captured=False

=== alpha2 artifact: runs\_designer\20260903-003655-666ba9c4\result.json ===
  result ruleset=bytefray-rules-4-alpha2 confidence=recorded winner=B
  replay ruleset=bytefray-rules-4-alpha2 confidence=recorded
  entrant A: alive=True core=N/A
  entrant B: alive=True core=N/A
```

Note the asymmetry is *correct*, not a bug: alpha1's real artifact shows
per-entrant core integrity (it is a `VULNERABLE_CORE_RULESET_IDS` member);
alpha2's shows `core=N/A` (it never was a member — the same fact §F.1's
finding depends on). This is the T-9 guarantee working exactly as
required, proven against real corpus data with the registry narrowed to
three identities.

### M.2 Replay History indexing and filtering

A full `ReplayHistoryService.rebuild()` was run against this checkout's
real `runs/` directory (isolated `cache_path`, real `data_root`), then
queried by `ruleset_id`:

```
rebuild took 245.5s, committed=True
bytefray-rules-4-alpha1: 12782 entries indexed
bytefray-rules-4-alpha2: 7 entries indexed
bytefray-rules-4: 1910 entries indexed
```

These counts match the Phase 2B.8 audit's own independently-measured
corpus distribution exactly (§N.2 of that report), confirming indexing,
filtering, and attribution all work correctly with the executable registry
narrowed to `{bytefray-rules-1, bytefray-rules-2, bytefray-rules-4}` — no
executable policy was needed for any of it.

---

## N. Ruleset 4 frozen-control qualification

All of the audit's §E.3 protective files were re-run and confirmed
passing (some converted/adapted per §C/§I, all preserving their
protective claims):

| File | Cases | Status |
| --- | ---: | --- |
| `test_v4_stable_ruleset_equivalence.py` | 27 | Converted to frozen-golden (§C); passing |
| `test_v4_runtime_default_ruleset.py` | 10 | Local frozen-policy reconstruction (§I); passing, unmodified in substance |
| `test_v4_historical_immutability.py` | 5 (was 4) | Converted to fixture-backed + reformulated (§C.1); passing |
| `test_v4_alpha2_placement.py` | 67 | T-4 masked-default rows updated (§I); passing |
| `test_v4_alpha2_scheduler.py` | 18 | Local frozen-policy reconstruction (§I); passing, unmodified in substance |
| `test_v4_process_semantics.py` | 5 | Local frozen-policy reconstruction (§I); passing, unmodified in substance |
| `test_v4_trace_equivalence.py` | 2 | Re-pointed; passing |
| `test_v4_production_integration.py` | 24 | Re-pointed (default param + 3 explicit sites, 1 evaluation cell-count assertion corrected for methodology difference); passing |

`resolve_ruleset_policy("bytefray-rules-4")` still returns fields
identical to pre-phase: `seeded` / `round_robin` / `chunked` / chunk 2 /
rotate `True` / API `{2}` / python-only — unchanged, since nothing in this
phase touched `RULESET_V4`'s construction (`ruleset_policy.py`'s `RULESET_V4`
object literal is byte-for-byte identical before and after). **No Scope-B
cleanup modified Ruleset 4's gameplay policy** — the mutation-sensitivity
demonstration in §C.4 is the direct behavioral evidence for this claim,
not merely the absence of a diff.

---

## O. Defaults verification

```
omitted API v2 python -> bytefray-rules-4
omitted API v1 python -> bytefray-rules-2
omitted VM             -> bytefray-rules-1
OMITTED_RULESET_CANDIDATES -> ('bytefray-rules-2', 'bytefray-rules-4', 'bytefray-rules-1')
DEFAULT_DESIGNER_RULESET_ID -> bytefray-rules-4
```

All unchanged from pre-phase — `OMITTED_RULESET_CANDIDATES` and
`DEFAULT_DESIGNER_RULESET_ID` were never edited by this phase, confirmed
by `git diff --stat` showing no hunk touching either definition.

---

## P. Collection-count reconciliation

| Checkpoint | Collected | Files |
| --- | ---: | ---: |
| Baseline (post-2B.9, `--collect-only`, before any change) | 3,444 | 148 |
| Final (`--collect-only`, after every edit in this report) | **3,440** | **148** |

**Exact arithmetic, baseline to final** (every line independently
verified against this report's own §C/§C.1/§F/§F.1/§G.3/§I/§J):

| Change | Delta |
| --- | ---: |
| `test_v4_stable_ruleset_equivalence.py` converted (§C) | 0 |
| `test_v4_historical_immutability.py` converted, 2 tests → 3 (§C.1) | +1 |
| Nine spectator/client/trace-equivalence files re-pointed (§F) | 0 |
| `test_designer_workflows.py`: 1 parametrize test (2 cases) → 1 single-case test; 1 parametrize test (2 cases) → 4 cases (§F, §G) | +1 |
| `test_ruleset_agent_compatibility.py`: 6 rows removed + 6-case negative test added; 2 rows removed + 2-case negative test added (§J) | 0 |
| `test_agent_evaluation_v4.py`: 2 tests removed + 2-case negative test added (net 0); 1 test removed, no replacement (§G.3, §J, §K) | −1 |
| `test_agent_test.py`, `test_v4_production_integration.py`, `test_v4_alpha2_placement.py`, `test_v4_alpha2_scheduler.py`, `test_v4_runtime_default_ruleset.py`, `test_v4_process_semantics.py`, `test_v4_interleaved_scheduler.py`, `test_cli_characterization.py`, `test_tournament_service.py`, `test_agent_evaluation_v2.py`: renamed/re-pointed only (§E, §I, §K) | 0 |
| `test_ruleset_policy.py`: 1 test removed, 1 replacement added (§G.3) | 0 |
| `test_designer_ruleset_options.py`: 1 whole test removed; anti-drift parametrize shrank 30→18 as `DESIGNER_RULESET_OPTIONS` narrowed 5→3 (§G.3) | −13 |
| `test_v4_alpha2_integration.py` removed whole (§G.1) | −8 |
| `test_v6_phase2b10_scope_b_v4_alpha_retirement.py` added (§J) | +16 |
| **Total** | **−4** |

`3,444 − 4 = 3,440` — matches the independently re-measured final
collection total exactly, via a per-file collection reporter summed twice
(once during the reconciliation pass, once in the final canonical
qualification run in §Q).

This phase intentionally did not target the charter's illustrative
"3,395–3,410" sanity range: like Phase 2B.9's own tripwire deviation, that
range predates several decisions this implementation had to make on the
evidence (the fixture-backed conversion in §F.1, the frozen-policy
reconstructions in §I, the T-4-class trap in §K) — the charter itself
states such a range is "a sanity range, not a target," and every
deviation from it is accounted for, line by line, in the table above.

---

## Q. Canonical pytest/ruff/mypy qualification

Per this repository's standing integrity protocol: HEAD SHA and SHA-256
digests of every `.py` file under `engine/src/battle_engine/` and
`app/services/` were recorded immediately before the final run
(`8244e6b588397206d482ddaf2245201f5f09d80d`), and re-verified
byte-for-byte identical immediately after (`diff` of both hash listings:
empty). `git status --short` was captured before and after; the only
difference was the removal of a basetemp directory deliberately deleted
between runs (see below) — no external process mutated the checkout.

### Q.1 A real regression caught and corrected by this protocol

The *first* full canonical run (against the tree as it stood immediately
after all Scope B edits) reported 3 failures, all in the same root cause:
`engine/src/battle_engine/data/starter_agents/v4_quorum/README.md` — a
**content-hash-pinned bundled starter artifact** — had been edited (§S,
correcting a stale "pass an explicit historical ruleset" sentence) without
recognizing that its packaged content is pinned by
`CURRENT_STARTER_DIGESTS['v4_quorum']` and must stay byte-identical to a
root-level `agents/v4_quorum/` mirror
(`test_v5_alpha1_phase_e_starter_refresh.py::test_current_bundled_content_matches_its_pinned_digest`,
`::test_missing_starter_installs_the_current_bundled_version`,
`test_v5_starter_agents.py::test_v5_starter_install_leaves_the_v4_population_byte_for_byte_unchanged`).
This is exactly the class of compatibility surface CLAUDE.md's "repo-specific
things to double-check before editing" warns about. The edit was reverted
(`git checkout -- engine/src/battle_engine/data/starter_agents/v4_quorum/README.md`),
restoring the file to its committed, pinned content; `git diff --stat` for
that path and its `agents/v4_quorum/` mirror confirmed no divergence
remained. The three affected tests were re-run standalone (83/83 passed
in the containing files) to confirm the fix before the full suite was
re-run from a clean baseline. No other pinned/bundled starter file was
touched by this phase (confirmed by `git status --short` showing only
`agents/viper/agent.py` — a non-pinned, untested repo-root example agent
— modified under `agents/`).

### Q.2 Full canonical suite

`python -m pytest -q --basetemp=.pytest-tmp`, one isolated invocation, no
concurrent pytest process, run against the corrected tree:

```
collected: 3,440
passed:    3,420
skipped:   20
failed:    0
errors:    0
```

Skip count (20) matches the pre-phase baseline exactly — no test's skip
condition changed. Exit code 0.

**mypy:**

```
mypy engine/src/battle_engine  -> Success: no issues found in 107 source files
mypy client/src/battle_client  -> Success: no issues found in 16 source files
```

**ruff:**

```
ruff check .  -> All checks passed!
```

No `--fix` corrections were needed this phase (unlike Phase 2B.9, which
needed two mechanical ones).

---

## R. Residue scan

`git grep` for both retired identity literals (`bytefray-rules-4-alpha1`,
`bytefray-rules-4-alpha2`) across every tracked `.py` file in the working
tree, excluding `docs/archive/`/`docs/releases/` (immutable historical
record, per standing policy). Every hit classified:

**Historical (archived research/history) — untouched, correct:**
`docs/archive/v4/`, `docs/archive/v5/` (30+ files across the v4/v5
alpha/beta/rc research record), `docs/releases/V4_0_0_ALPHA1_RELEASE_REPORT.md`,
`docs/ROADMAP.md`'s v4.0.0-alpha1/alpha2/rc1 release-note entries (§S),
`docs/V4_ALPHA2_DESIGN.md`, `docs/research/v6/V6_PHASE0_BASELINE.md`,
`V6_PHASE1_REPOSITORY_DIET_AUDIT.md`, `V6_PHASE2B7_RULESET3_ALPHA1_DISPOSITION.md`,
`V6_PHASE2B8_LEGACY_RULESET_RETIREMENT_AUDIT.md`,
`V6_PHASE2B9_SCOPE_A_RULESET_RETIREMENT.md` — prior phase reports and
design documents, immutable audit trail, never edited.

**Historical recognition (required reader/replay/evaluation compatibility)
— retained verbatim:** `rules.py` (both ID constants and their
provenance comments), `ruleset_policy.py` (retirement comments,
`_V2_METHODOLOGY_RULESET_IDS`/`_V4_METHODOLOGY_RULESET_IDS` membership,
`OMITTED_RULESET_CANDIDATES` docstring's historical mention),
`match_service.py` (the `_CORE_PLACEMENT_GUARDED_RULESET_IDS` retirement
comment), `agent_evaluation.py` (methodology-table docstrings, the
validation allow-list's own retirement comment, `resolve_v4_seed_geometry`'s
docstring, a schema-attribution comment at line 4209 describing how a
historical `rules_compatibility_id` value maps to schema fields),
`app/services/replay_history_presentation.py` (`_readable_ruleset`'s
shape-derived docstring example), `app/widgets/agent_combo.py` (a
comment explaining why kind alone cannot distinguish two Rulesets — still
accurate: the historical fact that both were once Python-only-and-alike
remains true), `engine/src/battle_engine/placement.py` (the frozen
`"bytefray-rules-4-alpha2:placement:"` domain-separation payload — a fixed
algorithmic constant that **must never change**, not a currently-offered
identity claim; and a provenance comment), `client/tests/test_replay_session.py`
(a hand-built schema-4 replay header, zero registry coupling, proven
independent of retirement in §Q — left unmodified, testing generic
process-anchor replay reconstruction using a retired-but-recognized ID,
which is *stronger* reader coverage than switching it to the control),
`engine/tests/test_spectator_analyzer.py` (same pattern, hand-built
header), `client/tests/test_fight_night.py` (a pure text-layout test using
the ID as an arbitrary label string, zero registry coupling),
`engine/tests/test_replay_integrity.py` (the ID used as an arbitrary
"different value" in a tamper-detection parametrize row, zero registry
coupling), `engine/tests/test_v5_replay_history_presentation.py` (label-
derivation table, shape-derived, zero registry coupling),
`engine/tests/test_evaluation_history_comparison.py` (hand-built
`EvaluationSummary` fixtures for the pure `align()` function, zero
registry coupling — verified directly in this session, §Q), and every
retained historical-recognition/frozen-fixture test named in §C/§C.1/§F.1/§I/§J.

**Golden/frozen provenance (documentation/metadata explaining a frozen
characterization's source):**
`test_v4_stable_ruleset_equivalence.py`'s and
`test_v4_historical_immutability.py`'s module docstrings and `EXPECTED`
table comments (§C, §C.1); `test_v4_runtime_default_ruleset.py`'s,
`test_v4_alpha2_scheduler.py`'s, and `test_v4_process_semantics.py`'s
local frozen-policy reconstruction comments (§I); the fixture directories
themselves (`engine/tests/fixtures/v4_historical_immutability/`,
`client/tests/fixtures/perspective_card_knowledge/`) and their
`.gitignore` negations.

**Negative-execution / product-surface test assertions (expected, by
design):** every `assert ... not in` / `pytest.raises(UnknownRulesetError)`
/ `pytest.raises(SystemExit)` site in `test_v6_phase2b10_scope_b_v4_alpha_retirement.py`,
`test_ruleset_agent_compatibility.py`, `test_agent_evaluation_v4.py`,
`test_agent_test.py`, `test_cli_characterization.py`,
`test_tournament_service.py`, `test_agent_evaluation_v2.py`,
`test_designer_ruleset_options.py`, and the four GUI-marked files (§L) —
these name the retired identities specifically *to prove* they are no
longer reachable, the intended residue of a completed retirement.

**Unexpected executable residue: none found.** Every production call site
of `resolve_ruleset_policy`/`_RULESET_POLICIES`/`PROCESS_RULESET_IDS` was
checked; none resolves, executes, or is reachable for either retired
identity. Every allow-list/membership table that named them was either
edited (registration, `_CORE_PLACEMENT_GUARDED_RULESET_IDS`,
`DESIGNER_AUTO_TRACE_RULESET_IDS`, the evaluation validation allow-list,
four CLI choice lists, three Designer option tuples) or confirmed to be a
historical-recognition/dual-use table that must keep their membership
(`VULNERABLE_CORE_RULESET_IDS`/`OBSERVABLE_CORE_RULESET_IDS`,
`_V2_METHODOLOGY_RULESET_IDS`/`_V4_METHODOLOGY_RULESET_IDS`).

**Comment corrections made for accuracy** (not executable, but were
actively misleading about current executability before this phase):
`README.md`'s "Historical Rulesets" section, `AGENTS.md`'s "Three v4
Rulesets now exist" note, `docs/RULES_V4.md`'s "remain executable" and
single-executable-control claims, `docs/COMPATIBILITY.md`'s
future-rulesets bullet, `docs/AGENT_AUTHORING.md`'s and
`docs/AGENT_API_V2.md`'s CLI/API guidance, `SECURITY.md`'s and
`docs/RESULT_SCHEMA.md`'s stale examples, `engine/src/battle_engine/agent_scaffold.py`'s
docstring, and `agents/viper/agent.py`'s design-rationale docstring and
usage example (§S). The one edit that touched a genuinely pinned artifact
(`v4_quorum/README.md`) was caught by the qualification run itself and
reverted (§Q.1) — not left in the final state.

---

## S. Documentation and changelog

Updated to no longer present V4 Alpha1/Alpha2 as available execution
choices, while preserving historical narrative where it describes a past
release's actual state:

* `CHANGELOG.md` — new `### Removed — V4 prerelease rulesets retired from
  execution` entry under `[Unreleased]`, above the existing Phase 2B.9
  entry; corrected that entry's own stale "alpha1/alpha2 remain
  executable" line.
* `docs/COMPATIBILITY.md` — new bullet + two new rows in the "Retired from
  execution / still recognised" table (renamed to cover both phases);
  corrected a stale "v4-alpha1" mention in the future-rulesets bullet.
* `docs/RULES_V4.md` — corrected the "single executable gameplay control"
  claim to name both retirement phases; corrected "remain executable" to
  describe the retirement and point at historical-recognition coverage.
* `README.md` — corrected the "Historical Rulesets" section's direct false
  claim that alpha1/alpha2 "remain executable and explicitly selectable";
  corrected the per-surface offered-Ruleset summary.
* `docs/AGENT_AUTHORING.md`, `docs/AGENT_API_V2.md` — corrected CLI/API
  guidance that told a reader to pass `--ruleset bytefray-rules-4-alpha1`/
  `-alpha2` explicitly.
* `AGENTS.md` — corrected the "Three v4 Rulesets now exist" architecture
  note, while preserving its valuable "frozen semantics, never re-bless a
  failing fixture" policy guidance in updated form.
* `SECURITY.md`, `docs/RESULT_SCHEMA.md`,
  `engine/src/battle_engine/agent_scaffold.py`,
  `agents/viper/agent.py` (a repo-root example agent's own docstring and
  usage example) — minor corrections to stale current-support phrasing.

**One attempted fix was reverted, not shipped:**
`engine/src/battle_engine/data/starter_agents/v4_quorum/README.md`'s
identical stale phrasing was also edited, but that file is a
content-hash-pinned bundled starter artifact; the edit was caught by
qualification and reverted rather than propagated into the digest tables
(§Q.1). Its stale "pass an explicit historical ruleset" sentence remains
in the final tree, an explicitly accepted, documented trade-off — fixing
it correctly (updating `SUPERSEDED_STARTER_DIGESTS`/`CURRENT_STARTER_DIGESTS`
and the root-level mirror in lockstep) is a real but separable change, out
of scope for a phase whose charter explicitly excludes "architectural
refactoring" (§23) and whose own reconciliation discipline requires never
forcing an unrelated fix through under qualification pressure.

Not touched (confirmed by `grep`, correctly already past-tense or
unrelated): `docs/RULES.md`, `docs/AGENT_LAB.md`, `docs/REPLAY_SCHEMA.md`
(accurately describes schema-version *reader* compatibility, not current
executability — both alphas' artifacts still need schema-v4 parsing),
`docs/ROADMAP.md` (its alpha1/alpha2 mentions are historical release-note
entries describing what was true *at that release* — left unedited per
this repository's standing rule against rewriting historical records in
place), `docs/archive/`, `docs/releases/` (immutable historical record).

---

## T. Quantified simplification

| Dimension | Before | After | Δ |
| --- | ---: | ---: | ---: |
| Executable ruleset identities | 5 | **3** | −2 |
| Production LOC (9 files: `ruleset_policy.py`, `match_service.py`, `designer_workflows.py`, `ruleset_options.py`, `agent_evaluation.py`, `cli.py`, `tournament_cli.py`, `agent_test.py`, `agent_scaffold.py`) | — | — | **−38 net** (116 ins / 154 del) |
| Research tools removed | — | — | 4 files, 1,847 LOC |
| Test files removed (whole) | — | — | 1 file, 8 cases |
| Test files converted (not deleted) | — | — | 2 files (`test_v4_stable_ruleset_equivalence.py`, `test_v4_historical_immutability.py`), 32 cases preserved |
| Test files with local frozen-policy reconstruction | — | — | 3 files (`test_v4_runtime_default_ruleset.py`, `test_v4_alpha2_scheduler.py`, `test_v4_process_semantics.py`), 33 cases preserved unmodified in substance |
| Test files re-pointed | — | — | 9 files, plus 1 fixture-converted (`test_perspective_card_knowledge.py`) |
| Test files pruned/fixed (case-level) | — | — | 4 files (`test_agent_evaluation_v4.py`, `test_ruleset_policy.py`, `test_designer_ruleset_options.py`, `test_v4_alpha2_placement.py`) |
| Test files added | — | — | 1 file, 16 cases |
| Canonical tests collected | 3,444 | 3,440 | −4 |
| GUI-marked test files updated (outside canonical count) | — | — | 4 files, 82 cases, all passing |
| Documentation files edited | — | — | 9 `.md` files + 2 Python docstrings (`agent_scaffold.py`, `agents/viper/agent.py`); 1 more attempted and reverted (§S) |
| Historical identities still recognized | — | — | Both, fully (§H, §J, §M) |

**"5 executable registrations → 3"** — matches the charter's §20 expected
conceptual change exactly. Remaining executable identities: Ruleset 1,
Ruleset 2, Ruleset 4.

---

## U. Phase 3 / Scope-C findings

Nothing new beyond what Phase 2B.8's own §X and Phase 2B.9's §R already
recorded; this phase's implementation confirms and extends rather than
adds to that list:

* **The execution/recognition table-conflation risk (§X.2 of the audit)
  materialized concretely three separate times in this phase** — the
  core-status tables (§H, inherited directly from the audit's own T-9
  warning), the evaluation-methodology tables (§D.1, a genuinely new
  instance this phase discovered by tracing consumers rather than
  assuming from the table's *name*), and `DESIGNER_AUTO_TRACE_RULESET_IDS`
  (§D, confirmed execution-only by the same tracing discipline). The
  audit's Phase 3 recommendation of an explicit, separate
  `historically_recognised_ids` table would have made all three
  determinations mechanical rather than requiring individual call-site
  tracing each time — this phase is a second and third confirmed instance
  of that recommendation's value, not just Phase 2B.9's first.
* **A T-4-class trap outside the audit's own enumerated list** (§K,
  `resolve_v4_seed_geometry`) was found only by running the test suite,
  not by reasoning about the function signature. This suggests the T-4
  family (functions that resolve `core_placement`/geometry by Ruleset ID
  string and fail *safe* rather than *closed*) may have further
  undiscovered members; a repository-wide audit of every
  `core_placement_mode`/`resolve_direct_match_starts`/
  `resolve_v4_seed_geometry`-shaped function for the same fail-safe-vs-
  fail-closed question would be a reasonable, narrowly-scoped Phase 3
  follow-up.
* **The V5 research program's own `runs/research_v5/` tooling
  (`tools/research/v5/*`) was confirmed untouched** — none references
  either retired v4 alpha; all run under `bytefray-rules-4`, unaffected.
* **Scope C's own cost is unchanged** — Ruleset 1/Ruleset 2/Agent API v1
  retirement remains a distinct, much larger product decision, not costed
  further by this phase.
* **The two-file identity-constant split** (`rules.py` vs.
  `ruleset_policy.py`) — unchanged by this phase, same Phase 3
  recommendation as before.

The four Ruleset-1 fallback problems (T-1/T-2/T-3/T-11) and Scope C itself
remain exactly as Phase 2B.8 left them — recorded there, not touched here,
per the charter's explicit §23 boundary.

---

## V. Unexpected findings

1. **`resolve_v4_seed_geometry`'s T-4-class fail-safe behavior** (§K) —
   not predicted by the audit or charter, found by execution.
2. **`client/tests/test_perspective_card_knowledge.py`'s real-match
   regression cannot be re-pointed to the stable control at all** (§F.1) —
   the audit's own P.3 table did not single this file out as needing
   anything beyond a routine re-point (it did not appear in the audit's
   measured Scope-B failure list at all, since the audit's narrowed-
   registry methodology measures *dispatch* failures, and this file's
   failure mode is a silently-passing-then-failing precondition guard,
   not a dispatch exception). Caught only because the charter's own
   evidence standard (assert the precondition actually occurred before
   asserting the code's response to it) was followed rather than assumed.
3. **`_V2_METHODOLOGY_RULESET_IDS` already contained `bytefray-rules-4-alpha1`
   before this phase** (§D.1) — a pre-existing, correct design fact (alpha1
   uses v2-style fixed placement) that made this table's dual-use nature
   immediately legible once traced, rather than something this phase
   introduced or needed to reason about from scratch.
4. **A documentation edit briefly broke a content-hash-pinned bundled
   starter artifact** (§Q.1) — editing
   `engine/src/battle_engine/data/starter_agents/v4_quorum/README.md`
   changed its packaged digest, which `CURRENT_STARTER_DIGESTS['v4_quorum']`
   pins and which must also stay byte-identical to a root-level
   `agents/v4_quorum/` mirror. Caught by the first full canonical
   qualification run (3 failures, all traced to this one file), reverted,
   and confirmed clean by a second full run — recorded here as a concrete
   instance of exactly the "retained compatibility surface" risk
   CLAUDE.md's editing checklist warns about, worth flagging for anyone
   touching bundled starter-agent files (`engine/src/battle_engine/data/starter_agents/**`)
   in a future phase: treat their content, including README files, as
   pinned unless the corresponding digest tables are updated deliberately.

---

## W. Final repository state

* Working tree: **not committed**, per the charter's §24 — left for
  review.
* `main`: untouched throughout (no command in this phase referenced it).
* `v6-research`: HEAD unchanged at `8244e6b588397206d482ddaf2245201f5f09d80d`
  (this phase's work is entirely uncommitted working-tree state, as
  instructed).
* Canonical suite: **3,440 collected / 3,420 passed / 20 skipped / 0
  failed / 0 errors** (exit code 0, second/final run, against the tree
  with the pinned-artifact regression already reverted — see §Q.1).
  `mypy` (engine + client): **clean, 107 + 16 source files, no issues**.
  `ruff`: **all checks passed**, no `--fix` corrections needed.
* Neither retired identity is executable. Both remain fully readable,
  attributable, indexable, filterable, and replayable, proven against both
  real on-disk historical artifacts (§M) and frozen fixtures (§C.1, §F.1),
  with permanent regression coverage for both sides of the contract (§J).
* Ruleset 4's gameplay is unchanged, proven by the frozen-golden
  characterization's own drift-sensitivity demonstration (§C.4), not
  merely the absence of a diff.
* HEAD SHA and SHA-256 digests of every `.py` file under
  `engine/src/battle_engine/`/`app/services/` were identical immediately
  before and immediately after the final qualification run, confirming no
  external process mutated the checkout during qualification (§Q).
