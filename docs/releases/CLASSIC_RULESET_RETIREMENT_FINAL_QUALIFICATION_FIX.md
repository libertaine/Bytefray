# Classic retirement final qualification fix — 2026-10-27

**Current disposition: READY FOR FINAL INDEPENDENT REVIEW.** The final P2
diagnostic correction and fresh qualification are recorded in the addendum
below. The earlier helper-only report is retained as history; its acceptance
of `validation_internal_error` for retired selection was incorrect and is
superseded by the addendum and `docs/specs/agent_validation.md` §6.3.

## Historical helper-only correction

**Verdict: READY FOR FINAL INDEPENDENT REVIEW.** The remaining P2 helper
expectation is corrected and passes bounded qualification. This is
self-verification; final independent verification and controlled commits are
the next steps. No staging or commits occurred.

## Root cause and correction

`run_negative_cases` in `tools/qualification/run_determinism_and_neg_cases.py`
still treated Classic as executable and expected Window Scout's SENSE
requirement to fail capability preflight. Retirement now rejects the Ruleset
before that preflight. The original helper independently reproduced an
`AssertionError` at its old diagnostic-code assertion.

The engine was not changed. Its existing library behavior is
`AgentValidationFailedError` with code `validation_internal_error`, stage
`internal`, exception type and chained cause `UnknownRulesetError`. The
diagnostic names `bytefray-rules-4` as retired and says it cannot run new
matches. The generic library diagnostic is the existing validation wrapper's
representation of this registry error; it is not a new dedicated retirement
diagnostic. The primary CLI rejects the argument earlier with exit **2** and
an explicit retirement message, empty stdout and no traceback.

| Case | Old expectation | Corrected expectation |
| --- | --- | --- |
| Window Scout with Classic | `agent_capability_unsupported` | Exact library code/stage/type/cause and retired identity/message; primary CLI exit 2 with retirement message |
| Rejected output | Not checked | Neither library nor CLI creates the requested trace or its output directory |
| Capability mismatch | Coupled to Classic execution | Separate isolated preflight with a manifest requiring SENSE and an empty available-capability set; exact `agent_capability_unsupported` and missing-SENSE message |
| Window Scout with Active Sensing | Successful Agent API v2 validation | Retained and passing |

The isolated capability case does not register a policy or execute agent code.
The existing capability suite also protects validation, worker and match
preflight, including rejection before agent import or output mutation. Its
passive-policy negative cases stop at preflight; no locked research is run.

Five new validation regression cases cover both supervised and unsupervised
requests, absent and pre-existing trace paths, and CLI argument rejection
before discovery. A preflight tripwire and agent-import marker prove rejection
ordering; existing trace bytes must survive unchanged.

## Exact task delta

1. `tools/qualification/run_determinism_and_neg_cases.py`: corrected retirement
   assertions, CLI rejection/artifact checks and isolated capability case.
2. `engine/tests/test_agent_validation.py`: five regression cases and the
   exception import. Its pre-existing arena-size correction is preserved.
3. `docs/releases/CLASSIC_RULESET_RETIREMENT_FINAL_QUALIFICATION_FIX.md`:
   this completion report.

All helper callers were inspected. The only external function caller is
`run_linux_native_workflow.py`; the helper's own module entry point runs both
determinism and negative cases and is Windows compatible. Both maintained
native workflows and `.github/workflows/` were searched for inherited
executable-Classic assumptions. No further such assumption was found; remaining
workflow mentions of “classic pygame” concern the Python dependency, not the
Ruleset. Neither native workflow script needed another edit.

The earlier schema-7, frozen-guard and compatibility-wrapper fixes and the
native workflow interface repairs remain unchanged.

## Executed qualification

All Python checks used the existing Python 3.13 environment with explicit
worktree-first engine/client/repository import paths. Pytest temporary and
cache paths were fresh absolute paths under the external evidence directory.
No repository evidence path was used as pytest basetemp.

| Check | Result |
| --- | --- |
| Original negative helper | Reproduced obsolete-code assertion failure; traceback retained |
| Corrected `run_negative_cases` call, matching the Linux caller's function | Exit 0; all fallback, retirement and capability assertions passed |
| Windows `python -m tools.qualification.run_determinism_and_neg_cases` | Exit 0; identical deterministic replay hashes, 103 replay lines and 1,600 logical trace records; all negative cases passed |
| Five new focused regression cases | 5 passed, 44 deselected |
| Bounded regression, nine modules | **335 passed**, no failures, errors or skips |
| Native workflow syntax/import audit | Both compile; all 31 Linux and 21 Windows imported modules/members resolve; Windows module imports safely |
| Helper syntax/import audit | Compiles; 17 imported modules/members resolve |
| `ruff check --no-cache .` | Passed |
| Engine mypy | Passed, 107 source files |
| Client mypy | Passed, 20 source files |
| Helper mypy | Passed, one source file |

The 335-case regression set comprises `test_agent_validation`,
`test_v6_alpha_m1_policy_capabilities`, `test_v6_alpha_m1_2_window_scout`,
`test_ruleset_policy`, `test_runtime_default_ruleset`,
`test_evaluation_identity_contract`, `test_v4_k1_capture_byte_identity`,
`test_v4_stable_ruleset_equivalence` and `test_v5_agent_parameters`.
The focused five cases overlap this set; do not add their totals.

All **15 K1**, **23 promotion** and **12 Phase-C** passive record guards
passed. Their three original literal tables compare equal as ASTs to expected
HEAD, with unchanged record counts. Historical schema-7 reconstruction passed
in the unchanged identity-contract module, alongside six cross-version golden
identity/history cases and the guard against authorizing Classic execution.

Live registry inspection confirms that `bytefray-rules-6-alpha1` is the sole
product Ruleset and omitted-selection default. Classic is absent from the
executable registry. The 15 retained identities include research identities;
they are not additional product choices.

## Git and evidence integrity

Branch remains `feature/retire-classic-ruleset`, with no upstream, at
`f127be70e7ed88449c1b737f4675e1453ec8de45`.
The inherited index patch, index entries and all refs remain byte-identical to
the pre-edit snapshot. Of 1,946 captured existing source/data files, only the
two listed Python files changed; 1,944 remain byte-identical. The report is new.
Protected tracked research, fixtures, archives, starter sources, release inputs
and earlier reports are among the unchanged paths. No research execution or
frozen-evidence amendment occurred.

All 316 captured files in the prior remediation evidence root and 2,527 in the
prior continuation evidence root retain their pre-task hashes. No previous
evidence directory was cleaned or overwritten.

Evidence, command records, reproduction traceback, logs, JUnit, baseline
patches/hashes, import audit and integrity audit are retained at:

`C:\Users\rasat\AppData\Local\Temp\bytefray-classic-final-p2-1sov1agm`

## P2 disposition and limits

The reported P2 mismatch is closed by implementation self-verification and is
ready for final independent review. No substantive regression was found in
the bounded checks. No skip or engine diagnostic change was introduced.

Native Linux/X11 qualification remains outstanding. The Linux session runner
executes a GUI session at module scope, so only its syntax and imported members
were checked here; the complete runner was not imported or executed on Windows.
The corrected shared helper did execute on Windows. Neither native GUI workflow
was rerun for this helper-only repair.

The full headless suite, packaging, installer and release qualification were
not repeated. Earlier documented baseline E8 failures, Windows
`0x8001010d` diagnostic and other release gates are unchanged. E9 remains LOCKED
and Requirement C remains NOT ESTABLISHED. This result does not promote any
release qualification status.

No stage, commit, merge, push, tag or publication occurred.

## Final P2 diagnostic correction — 2026-10-27

The independent review at
`C:\Users\rasat\AppData\Local\Temp\bytefray-classic-final-independent-xlswvtap\REVIEW.md`
closed the four original retirement findings but identified one remaining
diagnostic defect. This addendum records its narrow correction and implementation
self-verification. Final independent review is still required before controlled
local commits.

### Root cause and diagnostic contract

`_validate_agent` resolved the explicit Ruleset at its former line 279 without
handling `UnknownRulesetError`, a `LookupError` subclass. The exception escaped
to `validate_agent`'s generic `except Exception` at former lines 719–727, which
reported `validation_internal_error` / `internal`. That catch-all predates
retirement, but §6.1 of the validation specification reserves it for unexpected
orchestration failures. Unknown or retired selection is an expected input error.

Only the resolver call now catches `UnknownRulesetError` and translates it to
`AgentValidationFailedError` with **`ruleset_unavailable` / `configuration`**.
The taxonomy had no existing code describing unavailable Ruleset selection:
agent discovery, manifest, capability and action codes describe other failures.
The new narrowly defined code is documented in the existing diagnostic table and
§6.3 of `docs/specs/agent_validation.md`; `configuration` is the established
request-error stage used by match diagnostics. The `RuntimeDiagnostic` wire
shape, exception hierarchy and generic internal handler are unchanged.

| Request | Before this correction | Corrected |
| --- | --- | --- |
| Retired `bytefray-rules-4` | `validation_internal_error` / `internal` | `ruleset_unavailable` / `configuration` |
| Unknown `unregistered-ruleset` | `validation_internal_error` / `internal` | `ruleset_unavailable` / `configuration` |
| Unexpected orchestration exception | `validation_internal_error` / `internal` | Unchanged |

Both expected failures retain `exception_type=UnknownRulesetError`, the original
chained cause and the exact pre-correction message, verified by before/after
probes. Classic still says:

> Ruleset 'bytefray-rules-4' is retired and cannot run new matches. Bytefray 5.1.0-alpha.1 still runs it; its recorded artifacts remain readable.

Resolution still follows discovery/kind/API checks and precedes capability
preflight, import, worker startup and trace opening. The five earlier regression
cases remain, including both timeout modes, preflight tripwire, import marker,
absent output directories and preserved existing trace bytes. CLI invalid
selection still exits **2**, with empty stdout, explicit retirement text or
argparse's unknown-choice message, no traceback and no execution artifacts.
No result, replay, trace or output directory is created by rejected validation.

Six additional regression cases cover unknown-ID library/CLI handling and
unexpected orchestration failures. Resolver `RuntimeError` and generic
`LookupError` remain internal. An `UnknownRulesetError` unexpectedly raised by
capability preflight also remains internal, proving the new handler is confined
to Ruleset resolution. Their library and CLI checks retain the internal code,
stage and exception detail without a raw traceback.

### Changed-file inventory for this correction

1. `engine/src/battle_engine/agent_validation.py`: local typed resolver handler
   and public diagnostic documentation.
2. `docs/specs/agent_validation.md`: unavailable-selection taxonomy and contract.
3. `engine/tests/test_agent_validation.py`: correct the five retained cases'
   expectations and add six unknown-ID/internal-error regression cases.
4. `tools/qualification/run_determinism_and_neg_cases.py`: correct the shared
   helper's code/stage assertions and explanatory comment.
5. `docs/releases/CLASSIC_RULESET_RETIREMENT_FINAL_QUALIFICATION_FIX.md`: this
   addendum and explicit supersession of the earlier diagnostic interpretation.

### Fresh qualification

Python 3.13.14 used explicit worktree-first imports. All pytest basetemp/cache
paths were unique absolute external paths beneath this task's new evidence root.
The full campaign and native GUI workflows were not repeated.

| Check | Fresh result |
| --- | --- |
| Focused retirement/unknown/internal regression selection | **11 passed**, 44 deselected |
| Bounded regression collection | **397 passed**, no failures, errors or skips |
| Direct `run_negative_cases`, matching the Linux caller | Passed |
| Windows `python -m tools.qualification.run_determinism_and_neg_cases` | Passed; equal replay SHA-256, 103 replay lines, 1,600 logical trace records |
| Both native scripts: diagnostic-assumption inspection and syntax compilation | Passed; neither hardcodes the internal diagnostic; neither needed an edit |
| `python -m ruff check --no-cache .` | Passed |
| Engine / client / helper mypy | Passed: 107 / 20 / 1 source files |
| Frozen table AST comparison against expected HEAD | 15 K1, 23 promotion, 12 Phase-C and 90 E3 rows equal their original values |

The bounded collection contains the prior ten-module independent collection
(`test_agent_validation`, `test_v6_alpha_m1_policy_capabilities`,
`test_v6_alpha_m1_2_window_scout`, `test_ruleset_policy`,
`test_runtime_default_ruleset`, `test_evaluation_identity_contract`,
`test_v4_k1_capture_byte_identity`, `test_v4_stable_ruleset_equivalence`,
`test_v5_agent_parameters`, `test_evaluation_planning_matrix_equivalence`), plus
`test_agent_workflows` and the two passive E3 corpus metadata tests. The 11-case
focused run overlaps the 397 cases; do not add their totals.

Existing capability coverage rejects a SENSE-requiring agent under the registered,
executable passive research policy before execution, and validates the same agent
under Active Sensing. The helper's isolated capability mismatch remains covered.
The E3 checks were passive metadata/AST checks; its live corpus was not executed.

Live registry inspection confirms Active Sensing is the only product Ruleset and
Classic remains absent. Historical schema-7 identity/history tests pass, including
seed-1/arena-512 geometry **(380, 263)** and rejection of new Classic evaluation.
Historical interpretation remains independent of executable registration. The
15 K1, 23 promotion and 12 Phase-C passive guards pass; all 90 E3 golden rows
remain unchanged. No goldens, assertions, skips or frozen guards were weakened.

### Preservation, evidence and remaining gates

Branch remains `feature/retire-classic-ruleset`, without an upstream, at
`f127be70e7ed88449c1b737f4675e1453ec8de45`. The inherited index patch, index entries,
all refs and HEAD compare byte-identical to the pre-edit snapshot. Of 1,947
captured existing source/data paths, only the five inventory paths changed;
the other **1,942** retain their hashes. No new unignored source path was added.

All **1,347** captured files in the prior final-P2 and independent-review evidence
roots retain their pre-task hashes. The older retained manifests also verify all
**316** remediation files and **2,527** continuation files, with zero mismatches.
Protected research, fixtures, archives, agent sources, release/build inputs and
other inherited work remain intact. No previous evidence directory was cleaned
or overwritten.

Fresh logs, JUnit, before/after diagnostics, source/Git baselines, invariant and
preservation audits, and final file snapshots are retained at:

`C:\Users\rasat\AppData\Local\Temp\bytefray-final-p2-diagnostic-native-l82h2kou`

No substantive finding remains in this bounded correction's self-verification.
Final independent review, native Linux/X11, installer/release qualification,
the retained Windows `0x8001010d` diagnostic and the project-lead version decision
remain separate gates. Earlier baseline E8 findings are unchanged. **E9 remains
LOCKED; Requirement C remains NOT ESTABLISHED.** No E9 execution, staging, commit,
merge, push, tag, publication or version bump occurred.

**READY FOR FINAL INDEPENDENT REVIEW**
