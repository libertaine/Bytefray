# V6 Phase 2B.12 Scope C: Runtime Retirement

## Status

Implementation and independent qualification are complete in the uncommitted
`v6-research` working tree. No commit, push, merge, rebase, tag, upload, or
publication was performed.

Scope C retires new execution for:

- `bytefray-rules-1` and `bytefray-rules-2`;
- Agent API v1;
- native VM/builtin/blob entrants; and
- creation of Ruleset-2 group evaluations.

`bytefray-rules-4` and Agent API v2 process agents are the only current
execution path. Historical result, replay, trace, package-inspection, and
evaluation-history data remain readable where their compatibility contracts
require it.

## Implementation history and forensic repair

This phase began as an in-progress Gemini implementation. Its reported
qualification was discarded. Independent review found that the tree did not
collect cleanly and that many test conversions had changed or removed current
coverage rather than retiring only obsolete execution.

The invalid conversions included malformed duplicate imports, duplicate
`declare_processes()` fixtures, list-valued API-v2 actions, accidental fixture
and process-ID renames, commented-out arena assertions, self-referential
evaluation-identity assertions, reset tests that no longer reached `reset()`,
and current Ruleset-4 artifacts edited into synthetic "legacy" fixtures.
Current replay analysis, status, renderer, evaluation, scaffold, CLI, policy,
tournament, revision, and worker coverage had also been deleted or weakened.

The Codex continuation restored that coverage, replaced synthetic history with
committed schema-correct historical fixtures, repaired production boundaries,
and then requalified serially. During that continuation Codex temporarily made
one wrong policy choice: it restored three Ruleset-2 benchmark corpora and five
content-addressed Agent API-v1 starters as active historical fixtures. The user
clarified that Phase 2B.12 had already settled their retirement. That
restoration alone was reversed; the following are deliberately deleted:

- `v2_baseline.json`, `v2_baseline_corpus.json`, and
  `v3_phase1_arena_action_grid.json`;
- `claimer`, `strider`, `hunter`, `wanderer`, and `adaptive`; and
- the obsolete Ruleset-1 and Ruleset-2 promotion-equivalence test modules.

Git history, archived documentation, historical releases, and committed
artifact fixtures preserve the old evidence. The live tree does not need their
executors.

## Final execution boundary

The repaired boundary has these properties:

- executable Ruleset registration contains only `bytefray-rules-4`;
- omitted Ruleset resolution fails closed except for a compatible Agent API-v2
  roster, which resolves to stable Ruleset 4;
- `SUPPORTED_AGENT_API_VERSIONS` contains only version 2;
- loading, validation, supervised workers, `agents test`, match execution,
  evaluation, tournament, and Designer launch paths reject API v1 before its
  lifecycle can execute;
- `agents test` performs the API-version rejection during discovery, before
  trace/result/replay artifacts can be created;
- the worker independently rejects a non-v2 reset request before invoking an
  agent lifecycle method;
- VM/builtin/blob manifests remain classifiable for inspection and clear
  negative diagnostics, but have no executable Ruleset;
- new group evaluation creation is rejected because its only methodology was
  Ruleset 2, while historical group evaluation adapters and fixtures remain
  readable;
- the scaffold emits only Agent API-v2 blank and annotated templates; and
- the current starter catalogue contains the six `v4_*` and four `v5_*`
  Agent API-v2 starters.

Ruleset-4 gameplay was not redesigned. `derive_agent_seed`, API-version seed
material, placement, process scheduling, action semantics, replay/result
identity, and frozen Ruleset-4 golden values remain intact.
`supervised_runtime.py` retains the diagnostic helpers still consumed by the
Ruleset-4 path.

## Historical and residual references

The final search was classified by behavior, not by a literal-zero rule:

| Classification | Disposition |
|---|---|
| Current execution | Retired API-v1, VM/blob, Ruleset-1/2, group-evaluation, and obsolete default branches were removed or made fail-closed. |
| Historical reader/provenance | Agent API-v1 data types, historical Ruleset IDs, replay `runtime_kind`, result/replay readers, evaluation v1/v2/group adapters, and immutable provenance constants remain. |
| Negative compatibility | Package inspection, manifest discovery, label rendering, and rejection tests retain old kinds/IDs so unsupported inputs produce specific diagnostics rather than crashes or fallback. |
| Archive/research/history | v3 research tools and their source inputs remain in the repository. They are not current product registration and are excluded from wheel, sdist, and frozen runtime payloads. |
| Ruleset-4 internal controls | Direct process-runtime research controls may still construct the shared historical `AgentAction` shape; loaded product agents pass the strict `_validate_v2_action` boundary and can emit only `ActionKindV2`. |
| Accidental residue | Generated rewrite scripts/logs, stale temp roots, unused imports, obsolete package expectations, and retired payload inclusions were removed. |

Historical alpha1/alpha2 fixtures and the permanent
`test_v4_stable_ruleset_equivalence.py` control remain unchanged in purpose.
Historical IDs are recognized by readers but are not selectable executors.

## Independent qualification

All pytest gates were run serially with separate temp roots. The final GUI
evidence is an offscreen Qt run, not a claim of native visual, UI Automation,
or Narrator qualification.

| Gate | Result |
|---|---:|
| Scope-C retirement boundary | 332 passed, 2 skipped (334 discovered) |
| Stable Ruleset-4 frozen control, exact eight-module set | 152 passed |
| Historical readers | 545 passed, 3 skipped (548 discovered) |
| Current product workflows | 925 passed, 5 skipped |
| Residual touched-file cluster | 429 passed, 3 deselected |
| Focused evaluation v4 lifecycle module | 31 passed |
| Full offscreen root/client GUI selection | 499 passed, 510 deselected |
| Final focused packaging/frozen-resource gate | 105 passed, 5 skipped |
| Ruff | `All checks passed!` |
| Engine mypy | success, 90 source files |
| Client mypy | success, 16 source files |
| Final canonical suite | **2911 passed, 18 skipped, 3 deselected** in 267.55 s |

The final canonical run discovered 2,932 cases. The unchanged GUI marker
selection deselected three client GUI cases, leaving 2,929 selected cases:
2,911 passed and 18 skipped. There were zero failures and zero errors.

Two earlier 2,905-pass canonical runs are superseded and are not final
qualification evidence: one predated the repaired GUI tree, and the other
predated the packaging-boundary repair below. The 2,911-pass run is the only
final canonical result.

The 499-pass offscreen GUI run remains authoritative because every later
product-code cleanup was behavior-neutral (unused imports and an equivalent
inlined protocol check), while later tracked changes affected packaging
manifests, package validation tests, and build scripts rather than GUI/runtime
behavior. The subsequently built unified and standalone Designer executables
also passed their isolated GUI startup smokes.

## Exact collection reconciliation

The Phase 2B.12 baseline had 3,443 discoverable cases in the canonical
testpaths. Its three GUI-marked client cases were deselected, producing the
recorded **3,440 selected** baseline. The final tree has 2,932 discoverable
cases and the same three deselections, producing **2,929 selected**. Therefore:

`3,440 -> 2,929 = -511 selected cases`

The identical `-511` applies to all discoverable cases (`3,443 -> 2,932`)
because the three marker deselections did not change. A clean `git archive
HEAD` export and the final working tree were collected with the same
environment and marker override; the following table records every module
whose collection changed.

| Test module | Baseline | Final | Delta |
|---|---:|---:|---:|
| `client/tests/test_replay_session.py` | 50 | 49 | -1 |
| `client/tests/test_replay_status.py` | 22 | 21 | -1 |
| `engine/tests/test_agent_evaluation_group_analysis_integration.py` | 10 | 0 | -10 |
| `engine/tests/test_agent_evaluation_multi_entrant.py` | 45 | 0 | -45 |
| `engine/tests/test_agent_evaluation_v1_schedule_identity_compatibility.py` | 4 | 0 | -4 |
| `engine/tests/test_agent_evaluation_v2_methodology.py` | 44 | 0 | -44 |
| `engine/tests/test_agent_evaluation_v4.py` | 30 | 31 | +1 |
| `engine/tests/test_agent_evaluation.py` | 68 | 66 | -2 |
| `engine/tests/test_agent_lab_integration.py` | 4 | 0 | -4 |
| `engine/tests/test_agent_test.py` | 54 | 52 | -2 |
| `engine/tests/test_agent_validation.py` | 45 | 44 | -1 |
| `engine/tests/test_agent_worker.py` | 15 | 16 | +1 |
| `engine/tests/test_beta3_group_designer_workflows.py` | 13 | 0 | -13 |
| `engine/tests/test_check_wheel.py` | 8 | 14 | +6 |
| `engine/tests/test_cli_characterization.py` | 20 | 13 | -7 |
| `engine/tests/test_default_python_agents.py` | 39 | 0 | -39 |
| `engine/tests/test_designer_ruleset_options.py` | 35 | 23 | -12 |
| `engine/tests/test_entrant_identity.py` | 10 | 5 | -5 |
| `engine/tests/test_evaluation_history_verification.py` | 33 | 31 | -2 |
| `engine/tests/test_evaluation_v2_methodology_pure_functions.py` | 0 | 4 | +4 |
| `engine/tests/test_extracted_components.py` | 10 | 2 | -8 |
| `engine/tests/test_frozen_scaffold_resources.py` | 16 | 10 | -6 |
| `engine/tests/test_match_services.py` | 8 | 2 | -6 |
| `engine/tests/test_native_match_service.py` | 12 | 6 | -6 |
| `engine/tests/test_ownership_accounting.py` | 4 | 2 | -2 |
| `engine/tests/test_python_runtime.py` | 40 | 0 | -40 |
| `engine/tests/test_python_scheduler_characterization.py` | 2 | 0 | -2 |
| `engine/tests/test_reference_agents.py` | 7 | 0 | -7 |
| `engine/tests/test_replay_reconstruction.py` | 18 | 16 | -2 |
| `engine/tests/test_ruleset_agent_compatibility.py` | 25 | 28 | +3 |
| `engine/tests/test_ruleset_persistence.py` | 20 | 19 | -1 |
| `engine/tests/test_ruleset_policy.py` | 47 | 32 | -15 |
| `engine/tests/test_ruleset_v1_equivalence.py` | 8 | 0 | -8 |
| `engine/tests/test_ruleset_v2_promotion_equivalence.py` | 12 | 0 | -12 |
| `engine/tests/test_ruleset_v2_runtime_compatibility.py` | 15 | 0 | -15 |
| `engine/tests/test_ruleset_v2.py` | 17 | 0 | -17 |
| `engine/tests/test_scheduler_characterization.py` | 7 | 0 | -7 |
| `engine/tests/test_starter_directory_validity.py` | 28 | 17 | -11 |
| `engine/tests/test_supervised_runtime.py` | 6 | 0 | -6 |
| `engine/tests/test_tournament_service.py` | 35 | 31 | -4 |
| `engine/tests/test_v01_characterization.py` | 6 | 0 | -6 |
| `engine/tests/test_v2_default_placement.py` | 28 | 0 | -28 |
| `engine/tests/test_v3_closeout.py` | 8 | 0 | -8 |
| `engine/tests/test_v3_phase0_benchmark_population.py` | 16 | 0 | -16 |
| `engine/tests/test_v3_phase0_evaluation_conditions.py` | 20 | 0 | -20 |
| `engine/tests/test_v3_phase1_parameter_grid.py` | 23 | 0 | -23 |
| `engine/tests/test_v3_phase3_offense_payoff_evaluation.py` | 21 | 0 | -21 |
| `engine/tests/test_v3_phase3_rescore.py` | 7 | 0 | -7 |
| `engine/tests/test_v3_phase4_defense_payoff.py` | 11 | 0 | -11 |
| `engine/tests/test_v3_phase7_confound_isolation.py` | 7 | 0 | -7 |
| `engine/tests/test_v4_alpha2_placement.py` | 67 | 61 | -6 |
| `engine/tests/test_v5_post_release_h1_parameter_consistency.py` | 19 | 17 | -2 |
| `engine/tests/test_windows_packaging_spec.py` | 28 | 24 | -4 |
| **Canonical total (including unchanged modules)** | **3,443** | **2,932** | **-511** |

Whole-module retirement accounts for 420 removed cases. Reductions in
surviving modules and resource-derived parametrization account for 106 more.
Fifteen focused cases were added or restored for the v4 lifecycle, independent
worker rejection, pure historical methodology helpers, current compatibility
boundaries, and packaging exclusions. Thus `-420 - 106 + 15 = -511`.

Modules whose coverage was repaired without changing their total collection
do not appear in the table; their restored assertions are nevertheless covered
by the focused gates and final canonical run.

## Packaging and frozen-build qualification

The initial packaging inspection found a stale release gate:
`tools/check_wheel.py` still required retired VM/API-v1 starters and API-v1
templates. Broad setuptools `data/**/*` collection also shipped retained
research-only API-v1 agents and benchmark inputs. These were packaging defects,
not reasons to delete archive/research source from the repository.

The final packaging boundary now:

- explicitly includes only the two Agent API-v2 scaffold templates and ten
  current starter directories;
- rejects retired executor modules, API-v1 templates/starters/reference
  agents, benchmark corpora, and v3 disposable research agents in a wheel;
- prunes the same research-only material from the sdist; and
- exercises exactly the two current scaffold variants in Windows and Linux
  build scripts.

Fresh wheel and sdist builds succeeded. Exact archive inspection reported:

- zero forbidden retired execution resources;
- ten current starter manifests;
- two current template manifests; and
- eleven sampled historical result/replay/evaluation-reader files retained in
  the sdist.

The normal Windows PyInstaller build produced all four executables and passed:

- bytecode/cache exclusion;
- unified and standalone Designer GUI startup smokes;
- blank and annotated API-v2 scaffold creation;
- validation of both frozen-created agents; and
- post-smoke distributable-tree residue checks.

All four frozen payload trees contained zero forbidden retired data. The
unified, CLI, and Designer trees each contained ten current starters; the
unified and Designer trees contained both current templates. Recursive archive
inspection of the unified executable found the v1/v2/group evaluation adapters,
replay history, replay, and result readers, while the retired `builtins`,
`instructions`, `match`, and `reference_agents` executor modules were absent.

## Before and after

Before Scope C, the active product carried multiple retired selection,
dispatch, lifecycle, fixture, starter, and package-data paths alongside the
Ruleset-4 process runtime. Tests frequently proved old executors by running
them, and several GUI paths still offered or synthesized obsolete choices.

After Scope C, one Ruleset and one Agent API generation execute. Compatibility
code is limited to readers, provenance, inspection, and explicit negative
boundaries. Research inputs remain identifiable as research, not shipped
runtime payload. The final source, test, GUI, wheel/sdist, and frozen-build
evidence all exercise that same boundary.

## Repository integrity at handoff

- Branch: `v6-research` at `b6d2e09c683e561485764cd10245ce1c864694b2`.
- Local `main` remains at `82549f9c3ccbdb2e13b8165b32afef00def4a8f2`,
  identical to `origin/main`; `v6-research` is 20 commits ahead of it.
- `origin/v6-research` is one documentation-only commit ahead of the local
  branch. It was deliberately not pulled into this dirty implementation tree.
- Final porcelain status contains 198 entries: 131 unstaged modifications,
  38 unstaged deletions, 25 inherited staged deletions, and four collapsed
  untracked entries (six intended files: this report, one provenance README,
  one new pure-function test module, and three frozen fixture files).
- `git diff HEAD --check` exits cleanly; line-ending conversion notices are
  informational and no whitespace error is reported.
- `.claude/settings.local.json` remains present, ignored through
  `.git/info/exclude`, untracked, unstashed, and uncommitted.
- Zero Python/pytest processes, zero `.pytest-tmp*` roots, zero Phase 2B.12
  scratch roots, and zero generated qualification logs remained after cleanup.
