# Bytefray V6 — M2-2A targeted blocker investigation 01

2026-10-15, America/Indianapolis. **READY FOR SCOPE AMENDMENT.**
**M2-2 technical acceptance remains HOLD. No correction implemented.**

The Development Test failure is an obsolete CLI allowlist, inherited from HEAD,
which rejects explicit Alpha 1 before existing capability/runtime checks execute.
The worker failure is a reproducible sandbox process-observation failure, also
present without Keeper. The unchanged regression passes outside the sandbox on
both candidate and HEAD; no worker production correction is indicated. Native
authoring/replay qualification and a clean final broader run remain outstanding.

## 1. Authority and preservation

This investigation implements only the lead's bounded diagnosis/scope-preparation
instruction. The accepted [Scope Revision03](V6_ALPHA_M2_SCOPE_CONTRACT_03.md),
[Checkpoint B01](V6_ALPHA_M2_CHECKPOINT_B_01.md),
[M2-2 Implementation Record01](V6_ALPHA_M2_2_IMPLEMENTATION_RECORD_01.md),
and retained M1 acceptance govern. Their historical pending-approval language is
preserved; current authorization is not manufactured by editing those records.
Architecture, existing agent-test/scaffold specifications, relevant wire-contract
documentation and the actual CLI/Designer/runtime routes were inspected.

| Check | Result |
| --- | --- |
| Checkout / branch | `D:/Projects/BATTLE2/work/v6-m2-clean` / `v6-m2-clean` |
| HEAD | `f79a74be1d486f042d260bea672305b9abb27aa5` |
| HEAD tree | `d4f2c73cbd3965762e61316567537e173503ff8a` |
| Index raw SHA-256 | `b77a600d7e0c4e5679798a787e0b392b9994a5ae95a5b8841c4f0192bf6ee00b`; unchanged; staged diff empty |
| Recorded upstream | `origin/v6-research`, same SHA, local ahead/behind 0/0; no fetch/live-remote claim |
| Other refs | All recorded refs unchanged, including divergent local `v6-research` |
| Inherited/candidate files | All 23 entry files copied and raw-hashed: 16 candidate plus seven inherited files; zero changes during diagnosis |
| Original candidate receipt | All 16 files still match the prior implementation's retained `qualification/candidate_files/` copies |
| Governing inputs | Scope03 remains 37,938 bytes / `1b3e507a2593919ed64d43cad0d5ce673e734333529db1e936d5880b4a916eba`; B01 remains 22,023 bytes / `29e3883ab6a28995f1f105e9fb15f4e8091f0847930d38f2b1381a36d019f786` |
| Original demonstrations | All 32 entries in the retained artifact hash manifest match, covering four complete scenario bodies and captured sources |

Baseline comparison used `git archive HEAD`, extracted into the fresh ignored
`work/m2_2a_baseline_f79a74be_20261015/`. This is a source export, not a branch or
worktree operation. It contains no Keeper candidate. Archive SHA-256:
`1814fadf9cda7260ca58a67bb6e4abab8e984b94295ccd6659ae5b4190b00d32`.
Candidate and export have byte-identical `agent_test.py`, `test_agent_test.py`,
`agent_worker.py`, `process_containment.py`, `test_agent_worker.py`,
`app/agent_designer.py`, `app/services/ruleset_options.py` and
`app/widgets/ruleset_combo.py`. Observed baseline pytest collection/import paths
and supplemental child-worker paths resolve inside that export. Correct explicit
PYTHONPATH prevents the shared interpreter's editable installation from silently
selecting candidate sources.

The only added reviewable repository file is this report. Diagnostics, input
copies, the baseline export and fresh test scratch roots are ignored local
artifacts. No production or repository test file was edited. No merge, rebase,
reset, staging, commit, push, publication, M2-3 or research execution occurred.

## 2. Development Test root cause and safe correction boundary

The concrete launch chain is `AgentDesigner._on_test_agent()` in
`app/agent_designer.py` → `build_agents_command("test", ...)` →
`battle_engine.command._agents()` → `battle_engine.agent_test.main()` →
`_parser().parse_args()`. Designer already emits the selected explicit
`--ruleset bytefray-rules-6-alpha1` and preserves its data-root environment.

At `engine/src/battle_engine/agent_test.py:1031`, the parser has
`choices=[BYTEFRAY_RULESET_V4_ID]`. Argparse exits 2 with:

```text
argument --ruleset: invalid choice: 'bytefray-rules-6-alpha1' (choose from bytefray-rules-4)
```

This happens before roster resolution, capability preflight, worker creation or
match output. Fresh personal Keeper **and Scout** copies reproduce it without
creating a runs directory. The prior two native GUI failures have this same
diagnostic. This is not malformed Keeper metadata, a missing capability check,
an API-v2 restriction or a failure of Alpha 1 runtime dispatch. It is an inherited
integration gap exposed by the required full Development Test workflow; the
accepted M1 sensing contract itself needs no redesign.

Existing safe path:

- Explicit selections pass unchanged through `resolve_omitted_ruleset_for_agents`.
  Omitted selections consider only stable V4. `_entrant_compatibility_metadata`
  projects kind/API metadata; the authoritative manifest capability checks still
  occur in `_test_agent`, rather than trusting that projection.
- `_resolve_python_entrant` rejects retired/non-Python entrants;
  `_preflight_capabilities((tested_spec, opponent_spec), ruleset_id)` checks both
  manifests **before output-directory creation or agent import/reset**.
- `_resolve_default_parameters` uses the canonical parameter resolver for both
  entrants. `NativeMatchService` retains policy/composition checks and the
  existing supervised worker path. The API-v2 reference `v4_claimer` is legal
  under Alpha 1 without requiring SENSE or choosing a new opponent.

Fresh direct-service probes used the existing supervised `test_agent` service,
`timeout=5`, default 200-tick budget and unmodified runtime:

| Probe | Result |
| --- | --- |
| Personal Keeper vs internal reference, explicit Alpha 1 | Completed, tick limit 200; no diagnostics; parameters `scan_interval=4`, `perimeter_offset=27` |
| Personal Scout vs internal reference, explicit Alpha 1 | Completed at normal last-agent-standing termination, tick142/200; no diagnostics; defaults 4/64 |
| Ordinary API2 agent vs personal Keeper, explicit Alpha 1 | Completed, tick limit 200; Keeper defaults recorded in seat B; no diagnostics |
| Keeper as tested agent or explicit opponent, stable V4 | `agent_capability_unsupported`; requested output directory absent |
| Keeper, CLI ruleset omitted | Exit2, stable-V4 capability mismatch; no automatic Alpha 1 selection |
| Ordinary API2 agent, CLI ruleset omitted | Exit0; stable V4 reported |

Every successful direct-service result/replay pair passed `verify_result_replay`.
These are diagnostic development matches, separate from the four approved
Keeper/encroacher demonstrations and from native GUI acceptance.

The existing `test_agent_test.py` and M1 capability modules pass **94 tests**
unchanged. They cover substantial negative/default behavior but do not exercise
successful explicit Alpha 1 through this CLI. In particular the help test still
describes a single retained ruleset and never asserts Alpha 1 is selectable.

### Proposed scope amendment — for authorization, not yet implemented

Authorize only the following changes as a correction to M2-2's authoring route:

| Exact path | Permitted correction |
| --- | --- |
| `engine/src/battle_engine/agent_test.py` | Import the existing `BYTEFRAY_RULESET_V6_ALPHA1_ID` constant from `battle_engine.rules`; make the parser choices exactly stable V4 and Alpha 1; replace the adjacent obsolete help with stable-default/explicit-experimental guidance; correct the stale single-executable-combination comment in `main`. Preserve all execution, default, capability, timeout, parameter and exit-code behavior. |
| `engine/tests/test_agent_test.py` | Extend this existing module with real CLI Alpha 1 positive/default/negative coverage described below; update the help test's name/documentation/positive assertions while retaining every historical/research exclusion. No production-service mocks for the successful integration cases. |
| `tests/test_v6_alpha_m1_5_designer.py` | Retain both failing Keeper cases and strengthen their final Development Test checks to inspect canonical result/ruleset/default parameters, trace, correct Test replay association and earlier Advanced results. Add a bounded Scout Development Test regression using real QProcess; keep all additions GUI-marked. |

No additional production path is necessary. No CLI parameter override, reference
opponent change, ruleset registry/policy/default change or new schema is proposed.
Do not replace the two choices with the full registered ruleset set: that would
expose internal research identities. New unexpected failures require diagnosis
and another scope decision, not automatic file-boundary expansion.

Designer already offers Alpha 1 explicitly in Advanced/Development, starts at
stable V4, disables incompatible execution and never repairs a selection into an
experiment. Selecting Keeper must continue to require the user's explicit
selection. Advanced edits must continue to have no effect on Development Test's
manifest defaults. No functional GUI selection change is indicated. The comment
at `app/agent_designer.py:1364` still says Scope C offers only stable V4; this is
obsolete commentary, not a launch restriction, and does not require widening the
minimal production amendment. Collective ruleset-description and A/B/layout work
remain assigned to M2-4.

### Required correction tests

| Route / case | Required assertions |
| --- | --- |
| CLI explicit Alpha 1, personal Keeper and Scout vs reference | Real supervised native execution through `main`/command route; exit0, no tool/internal error; correct ruleset in printed output, replay header and result; valid result/replay digest, trace2, result2/replay4; canonical manifest defaults and no agent diagnostic. Run to requested limit or legitimate terminal condition, not a clipped receipt witness. |
| CLI explicit Alpha 1, ordinary tested agent vs explicit Keeper opponent | Whole roster accepted; both identities/defaults preserved; no special reference-only success. |
| CLI explicit V4 and omitted ruleset, ordinary API2 roster | Stable V4 remains the resolved/reported identity. |
| CLI explicit V4 and omitted ruleset, required-SENSE in either slot | Capability failure before import/reset and replay/result/trace creation; import/reset sentinels untouched, no output directory. Both candidate-first and opponent-only cases required. |
| CLI Alpha 1 with malformed capability metadata in either slot | Unknown version/name, duplicate required name and list-shaped block remain distinct `agent_manifest_invalid` errors before import/reset/artifacts; reuse the established malformed-value cases, without weakening existing coverage. |
| CLI retired/incompatible entrant metadata | API1, VM/blob and invalid kind/API combinations fail closed before execution/artifacts under explicit Alpha 1 as well as existing V4/omitted routes. Preserve established diagnostics. |
| Parser/help surface | Exactly two product choices; Alpha 1 explicitly selectable, V4 still omitted default. Unknown, retired and research IDs remain rejected with exit2, including the documented retired identities. Research identifiers may be used as rejected parser inputs only, never executed. |
| Real native Designer Keeper Test after Advanced edits | Click Test after existing copy/validate/edit/run/reopen checks; inspect Test's own canonical result, defaults 4/27 rather than Advanced overrides, selected/reported Alpha 1, trace and result-associated Test reopen. Prior Advanced output/path/settings labels remain available. Both existing Advanced seat cases remain. |
| Real native Designer Scout Test | Explicit Alpha 1 reaches the same CLI; defaults 4/64 recorded. No silent ruleset switch or Advanced parameter transfer. |
| Existing regression anchors | Re-run M1 capabilities, designer ruleset options, validation, scaffold/starter/refresh, Scout, sensing/capture/client and GUI adversarial anchors from Checkpoint B §4. Preserve normal forfeit/death/loss/init-failure exit contracts and stable/historical readers. |

Diagnostic direct-service success does not replace these post-amendment CLI and
GUI tests. A GUI label containing "Complete" alone is insufficient evidence of
defaults or artifact association. Existing launch-capture stubs verify the chosen
path but do not verify external viewer controls.

## 3. Worker-liveness diagnosis

Exact test:
`engine/tests/test_agent_worker.py::test_worker_does_not_survive_a_hard_kill_of_its_own_parent`.
The unchanged assertion fails at line 527:

```text
assert _pid_is_alive(worker_pid), "worker should still be running before the kill"
AssertionError: worker should still be running before the kill
```

Windows `_pid_is_alive` calls `tasklist /FI "PID eq <pid>"` and checks only
whether the PID string appears in stdout. It ignores nonzero return codes and
stderr. In this sandbox, `tasklist` returns code 1, empty stdout and
`ERROR: Access denied`. The helper therefore reports a live worker as absent.
The main test body never reaches its deliberate parent kill or post-kill
assertion. Its `finally` kills the disposable parent on failure.

Controlled runs used Windows AMD64 build 26120, Python 3.13.7, pytest 9.1.1 and
the same explicit repo interpreter. Every pytest invocation had a new absolute
basetemp/cache outside runs/evidence, verified beneath this checkout, and retained
command/environment JSON, log and JUnit. Windows pytest executions were sequential.

| Execution | Result |
| --- | --- |
| Candidate, isolated exact node, sandbox | 1 failed at pre-kill liveness assertion, 2.00s |
| Clean HEAD export, isolated exact node, sandbox | Same 1 failure, 2.18s |
| Candidate and HEAD export, observed exact node, sandbox | Each still fails unchanged; original tasklist result and assertions preserved |
| Candidate, full unchanged worker module, sandbox | 15 passed, 1 failed; same sole pre-kill failure, 9.94s |
| Candidate, isolated exact node, outside sandbox | **1 passed**, 2.39s; original test, no observer or patch |
| Clean HEAD export, isolated exact node, outside sandbox | **1 passed**, 2.43s; original test, no observer or patch |
| Candidate, full unchanged worker module, outside sandbox | **16 passed**, 10.16s; no skips, observer, assertion changes or production edits |

Observation used a local pytest plugin wrapping subprocess observation only.
It returned the original `tasklist` CompletedProcess unchanged, retained a
non-inheritable Windows worker process handle and recorded collection/import
paths. Before the assertion, `WaitForSingleObject(handle,0)` returned 258
(`WAIT_TIMEOUT`) and `GetExitCodeProcess` returned 259 (`STILL_ACTIVE`) on both
candidate PID 71652 and baseline PID 70204, even after tasklist denied access.
After the original test's cleanup killed the corresponding parent (exit 1), both
same process handles became signaled (wait 0, observed worker exit 0). The plugin
did not replace `_pid_is_alive` or cause either failed test to pass.

A separate supplemental lifecycle probe removed uncertainty about whether the
worker actually entered a hung callback. A fresh synthetic API2 agent writes a
disposable entry marker inside `reset`, then loops forever. On each source tree:
load returned OK; the marker was present; after 1.5s the parent was still running
and the worker handle was unsignaled/STILL_ACTIVE. The live binding type was
`_WindowsJobHandle`. Tasklist still denied access. Killing only that probe's
parent caused its worker handle to signal in approximately 0.002s, exit 0, without
emergency worker termination. Retained PIDs: candidate parent 50736/worker 22612;
baseline parent 29240/worker 42492. These synthetic runs are separate diagnostic
evidence, not replacements for the original regression or native GUI testing.

Conclusion: this failure is independently reproducible on the accepted current
HEAD without Keeper, and changes with the observation environment while source
remains identical. A timing increase or production cleanup change is not needed
to explain it. The evidence identifies denied tasklist observation; it does not
identify the particular Windows service/ACL responsible for that denial. The
unchanged native passes establish the actual regression check succeeds here when
run outside the restricted sandbox.

**Minimal corrective scope: no worker production or test edits.** Run this
regression in a native context where its real process probe works. Keep sandbox
failures and their environment disposition. Do not suppress, skip, weaken or
replace the test, and do not combine its isolated pass with the earlier broad
failure counts to fabricate a green broad run. Future optional test-probe
hardening would need a separate test-only scope decision; it is unnecessary for
the proposed parser amendment. The original test's child bootstrap also inserts
nonexistent `engine/engine/src` and `engine/client/src` paths; explicit correct
PYTHONPATH and recorded import paths exclude that fragility as this run's cause.

## 4. Qualification completion and evidence reuse

The accepted Scope §§3/7/10 and B2-01–B2-09 require the following M2-2 closure
work after any authorized correction. This plan does not start M2-5, M2-3 or a
new full campaign without its applicable authorization.

| Evidence partition | Retain / current disposition | Completion requirement |
| --- | --- | --- |
| Focused behavior/provenance | Original final 533 passing anchors/4 GUI deselected and final 48 Keeper cases remain valid for their recorded sources; selections overlap | Run new CLI tests and affected existing anchors first on the corrected candidate, plus native GUI nodes explicitly. Rebind exact dirty-source manifest and selections; do not sum counts. |
| Broad product regressions | Original 3,335 passed/1 failed/20 skipped/5 GUI deselected remains a failed broad run | Re-run the reconciled 137-module product selection plus any authorized test additions on the corrected candidate in a working native process-observation context; reconcile exact new/removed nodes, skips and markers. No ad hoc exclusions. The worker module now has separate native PASS evidence. |
| Compatibility supplement | Original 328 pass retained separately | Re-run the adopted compatibility supplement for final corrected-candidate qualification, keeping its manifest/results distinct from product and focused runs. Preserve V4 omitted/default/equivalence, retired refusal and historical readers. |
| Preservation/engineering | Original 329 historical raw pins and engineering checks retained as historical observations | Verify unchanged pins against preserved `b948540...`, old starter bytes/digests/order/customizations and exact approved diff. After final focused/broad checks run Ruff and separate engine/client mypy. Do not rerun scientific operations or reseal source pins. |
| Windows Keeper demonstrations | Four complete runs, two per seat, remain hash-verified with per-seat comparisons and source snapshots | Retain if captured Keeper/fixture, runtime, scenario verifier and fixed inputs remain identical. A parser-only amendment does not change the direct NativeMatchService demo route. Record a dependency/source-delta review; rerun only for relevant source/input drift or a concrete gap. Do not rewrite old manifests to call them new executions. |
| Linux Keeper demonstrations | Not executed | Four complete native runs: twice per seat, arena 512/Q8/seed 0/100 ticks, direct starts 0/91 with whole-role reversal, defaults 4/27; retain full replay/trace/result/common-v1 sidecar/executed sources and independent Keeper predicates. |
| Native Windows authoring/GUI | Existing two GUI cases fail at real Test after partial authoring/Advanced success; external viewer launch target was captured by a stub | Re-run the complete corrected copy→explicit-Alpha1 Validate→edit→Advanced full match→reopen→manifest-default Test workflow, both existing seat cases; verify overwrite/range/stable refusal, source/ruleset invalidation, prior-settings output and actual Test result association. Then launch the actual external replay viewer and exercise its supported controls/reopen. |
| Native Linux authoring/GUI | Missing; no Linux execution in this investigation | Independent affected engine and complete authoring/replay workflow under Qt xcb/SDL x11 on X11/Xvfb, including real CLI children and external viewer. Record display/focus/activation assistance. Startup/offscreen screenshots alone cannot close it. |
| Cross-platform logical comparison | Windows per-seat repeats available; no Linux pair comparison | Compare equivalent captured inputs and same-build logical world/observations/actions/terminal facts across Linux/Windows. Exclude only declared wall_time_ms, non-gameplay completion timestamps and diagnostic path text; hash every raw body independently. Do not demand raw result/trace or LF/CRLF equality. |
| Lead acceptance | Open | Map final exact nodes/artifacts to each B2 gate and obtain review of this candidate and limitations. Neither this report nor a scope amendment accepts M2-2 or starts M2-3. |

For both native platforms retain OS/architecture, Python executable/version,
dependencies, source/dirty diff, resolved Config, starts/roles/parameters, Qt/SDL
drivers, display/focus setup and resolved fonts. Exercise existing supported
keyboard/mouse pause/step/exchange stepping, reverse seek/restart, scrolling,
resize, close and result-associated reopen with correct delivered/omniscient
labels. Keep full interaction logs and authentic frames, original failures and
any focus assistance. Keep corrupt/missing-pair and optional-sidecar-only
fallback regressions. Use fresh dedicated data/output roots with no research
inputs or retained-data basetemp traversal.

B2 requires the accepted M1 viewer during Keeper qualification. The new A/B/Omni
selector, history/footer separation and all-view layout corrections at 900x650,
1000x700 and 1100x750 remain M2-4 implementation/M2-5 qualification work; do not
implement them to clear M2-2. Retain the current limitation explicitly. Keep the
accepted Windows COM observation and Linux X11 focus prerequisite; a new
functional failure still needs diagnosis. Human comprehension remains M2-6.
No release, installer, Wayland, full Python matrix or other-distribution claim.

## 5. Exact reproduction and retained evidence

New ignored evidence root:
`runs/v6_alpha_m2/m2_2a_20261015_diagnosis/`.
Original evidence remains under `runs/v6_alpha_m2/m2_2_20261015_review/`.

From this checkout, the exact sandbox isolated-node invocation was:

```powershell
$env:PYTHONPATH = "$PWD\engine\src;$PWD\client\src;$PWD"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:BYTEFRAY_ROOT = "$PWD"
& '.\.venv\Scripts\python.exe' -m pytest engine/tests/test_agent_worker.py::test_worker_does_not_survive_a_hard_kill_of_its_own_parent --basetemp=D:\Projects\BATTLE2\work\v6-m2-clean\.pytest-tmp\m2_2a_worker_candidate_01 -o cache_dir=D:\Projects\BATTLE2\work\v6-m2-clean\.pytest-cache\m2_2a_worker_candidate_01 --junitxml=D:\Projects\BATTLE2\work\v6-m2-clean\runs\v6_alpha_m2\m2_2a_20261015_diagnosis\m2_2a_worker_candidate_01.xml -vv --tb=long
```

This command documents an already-used disposable path; use a new label/path to
reproduce, never point pytest at evidence or reuse retained scratch as new input.
The baseline invocation changes cwd/PYTHONPATH to the export and uses the
`m2_2a_worker_baseline_01` label. Outside-sandbox commands use the same interpreter,
node, flags and source, with fresh `*_native` labels. `run_selection.py` retains
the exact expanded argv/cwd/environment identities in each `*_command.json`.
Its outer diagnostic wrapper exits normally after recording a failed pytest;
the embedded `returncode`, log and JUnit are authoritative, not the wrapper exit.

| Evidence | Contents |
| --- | --- |
| `preservation_before.json`, `preserved_inputs/`, `candidate_before.diff`, `refs_before.txt`, `status_before.txt` | Entry identities and all 23 exact input bodies |
| `preservation_after.json`, `preservation_exit.json` | Before-report and final preservation/source-comparison receipts |
| `baseline_HEAD.zip`, `preserve.py` | Exact HEAD source archive and preparation method |
| `m2_2a_worker_{candidate,baseline}_01.{log,xml}`, corresponding command JSON | Unmodified isolated sandbox failures |
| `m2_2a_worker_{candidate,baseline}_observed*`, `lifecycle_observer.py` | Unchanged failed assertion plus process handles, tasklist error, parent/worker exit and import/collection evidence |
| `hung_{candidate,baseline}/`, `hung_lifecycle.py` | Fresh synthetic agent, parent script, reset-entry marker, lifecycle states and stderr |
| `m2_2a_worker_{candidate,baseline}_native*`, `m2_2a_worker_module_native*` | Unmodified native passes; isolated baseline/candidate and full candidate worker module |
| `m2_2a_worker_module*` | Restricted-context module failure retained separately from native result |
| `development_probe.py`, `development_probe.json`, `development_data/` | Exact CLI refusals, supervised service positive/negative matches and complete artifacts |
| `m2_2a_development_existing*` | Existing agent-test/capability selection: 94 passed, 14.67s |
| `evidence_sha256.txt` | Raw hashes of final diagnosis evidence and this report |

An initial diagnostic runner launch used a wrong parent-directory index and
failed while trying to create a scratch parent outside this checkout; filesystem
permission checks blocked it before pytest or source writes. The local runner
was corrected, then verified to use only new scratch roots under this checkout.
This was diagnostic tooling, not a product failure or an omitted pytest result.

## 6. Decision requested

**READY FOR SCOPE AMENDMENT:** authorize the three exact paths and bounded
corrections/tests in §2. No worker correction is recommended; accept the retained
restricted-environment disposition and independent unmodified native evidence
for that blocker, while requiring final corrected-candidate broad qualification.

**M2-2 remains HOLD** until the authorized correction, required regression/native
qualification and lead review pass. Stop here for project-lead authorization;
this investigation grants no implementation, milestone-entry or publication
permission.
