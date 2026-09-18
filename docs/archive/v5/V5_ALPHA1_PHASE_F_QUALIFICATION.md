# Bytefray V5 Alpha 1 — Phase F Qualification

Date: 2026-09-09. This is a stopped release-qualification record, not a release
announcement. Product source was not remediated.

**ALPHA 1 PUBLICATION BLOCKED — REMEDIATION REQUIRED**

The candidate's frozen unified executable omits both Agent API v2 scaffold
template directories. Both supported API-v2 creation commands fail with exit
code 2. The same candidate's clean installed wheel successfully creates and
validates an API-v2 scaffold. Passing source tests and a successful executable
build therefore do not qualify the packaged product.

## A. Candidate identity

| Property | Recorded value |
| --- | --- |
| Branch | `v5-research` |
| CANDIDATE_SOURCE_SHA | `0dde69c9695c8c730fe190af23f6d92783072ffd` |
| Local `origin/v5-research` | Same SHA; no fetch performed |
| Phase E present | HEAD, `feat(v5): integrate parameter-driven designer workflow` |
| Product version | `5.0.0a1` |
| Gameplay | `bytefray-rules-4` |
| Qualification start | 2026-09-09 09:44:56 -04:00 |
| Host | Windows 11, build 26120, AMD64 |
| Python | CPython 3.13.14, MSC v.1944, 64-bit |
| Toolchain | pytest 9.1.1; Ruff 0.16.3; mypy 2.3.1; build 1.6.0; setuptools 84.0.0; wheel 0.48.0; PyInstaller 6.22.2 |
| GUI libraries in source/build environment | PySide6 6.11.2; pygame-ce 2.5.8 |
| Clean wheel environment | Bytefray 5.0.0a1 and PyYAML 6.0.3; no GUI extras |
| Source remained frozen | **YES** |

The initial attempt stopped on untracked local files. After the user reported
those resolved, branch, HEAD, local remote-tracking SHA, status, diff and index
checks were repeated. Status and `diff --check` were empty; `index.lock` was
absent. The index was 93,148 bytes, last modified 2026-09-09 09:04:29 local time.

The sandbox could not read the global Git ignore file. A per-command
`git --no-optional-locks -c 'core.excludesFile=' status --short` also returned
empty, without modifying configuration. An earlier diagnostic attempt to use
`NUL` as the excludes file failed; it changed no Git state. Normal status's
ignore-file warning is recorded, not treated as evidence of a damaged index.
The development interpreter could not start inside the sandbox; approved
execution outside it worked. No source repair was involved.

Builds used a clean export produced by read-only `git archive` of the exact
candidate SHA, extracted into
`build/phase-f-0dde69c-20260909/source`. New output directories isolated all
artifacts from older `dist/windows` and installer output. No stale output was
reused or deleted. This report was added only after all launched tests/builds
and diagnostic commands had terminated; it is **not part of the candidate SHA**.

### Current-version audit

| Source/surface | Finding |
| --- | --- |
| `pyproject.toml:10` | Canonical distribution version `5.0.0a1` |
| `tools/installer.iss:5,13` | `AppVersion` and `ReleaseTag` both `5.0.0a1`; filename would be `Bytefray-Setup-5.0.0a1.exe` |
| `battle_engine.project_info.get_project_info` | Reads `importlib.metadata.version("bytefray")` |
| `battle_engine.command._version_string` | Uses the shared project metadata |
| Development metadata/CLI | `5.0.0a1` |
| Built wheel metadata and sdist-generated wheel | `5.0.0a1` |
| Clean installed wheel CLI | `5.0.0a1` |
| Frozen unified CLI | `5.0.0a1`, API v2, result schema v1, replay schema v4 |
| Windows PE version resource | FileVersion/ProductVersion absent; the canonical spec supplies no separate version resource. No contradictory PE version found. |
| Phase B–E records and current parameter guide | `5.0.0a1` |
| README/CHANGELOG | Describe the published V4 stable release; no Alpha 1 release-note entry yet |

No current canonical product source using `5.0.0-alpha1` was found. Installer
comments explain a historical hyphenated tag convention, but the actual Alpha
1 defines use PEP 440 spelling. Historical V4 release/ruleset references and
per-agent `1.1.0` manifest versions are different identities, not product-version
mismatches. INSTALL/Linux installation examples still name RC2 artifacts and
link to README for the current release; they need release-documentation review
when a replacement candidate qualifies. No version string was edited.

## B. Source qualification

Every pytest run was sequential, with a distinct temporary root below the
ignored qualification directory and an isolated `BYTEFRAY_ROOT`.

| Gate | Passed | Failed | Errors | Skipped | Deselected |
| --- | ---: | ---: | ---: | ---: | ---: |
| Focused source gates | 516 | 0 | 0 | 0 | 0 |
| Focused Designer GUI gates | 60 | 0 | 0 | 0 | 0 |
| Full default headless suite | 3279 | 0 | 0 | 14 | 3 |
| Complete GUI/app selection | 340 | 0 | 0 | 0 | 6 |

Full headless elapsed time: 337.23 seconds. Complete GUI/app elapsed time:
43.49 seconds, with Qt offscreen and SDL dummy video. These are automated
GUI checks, not a claim of manual display/input qualification.

The focused source selection contained:

| Module (`engine/tests/`) | Passed |
| --- | ---: |
| `test_v4_stable_ruleset_equivalence.py` | 23 |
| `test_v4_alpha2_placement.py` | 67 |
| `test_v4_alpha2_scheduler.py` | 18 |
| `test_v4_runtime_default_ruleset.py` | 10 |
| `test_ruleset_policy.py` | 49 |
| `test_v5_alpha1_phase_b_engine_hygiene.py` | 8 |
| `test_v5_starter_agents.py` | 54 |
| `test_v5_agent_parameters.py` | 124 |
| `test_v5_alpha1_phase_e_starter_refresh.py` | 24 |
| `test_v5_alpha1_phase_e_designer_services.py` | 25 |
| `test_starter_agents.py` | 15 |
| `test_v4_production_integration.py` | 9 |
| `test_v4_historical_immutability.py` | 2 |
| `test_designer_ruleset_options.py` | 47 |
| `test_designer_third_entrant_command.py` | 9 |
| `test_replay_contract.py` | 15 |
| `test_windows_packaging_spec.py` | 17 |

Stable placement/scheduler/default/policy group: 167 passed. No golden fixture
was changed. R1/R2 ruleset, mortality and oracle searches over production
engine/client/app/agent paths returned no matches. Historical `v4_*` agent
paths have no diff against the Phase A execution baseline `eb1b389`; the
older stable-release comparison contains the already-recorded pre-Phase-A
Quorum ClassVar annotation change, not a Phase B–E gameplay change.

`ruff check .`: all checks passed. `mypy engine/src/battle_engine`: no issues
in 107 files. `mypy client/src/battle_client`: no issues in 16 files.

No atomic-rename flake occurred. Two qualification-harness mistakes are kept
visible: the first complete-GUI command named nonexistent
`engine/tests/test_linux_qt_smoke.py` and exited 4 with no tests run; its
corrected selection was `-m gui tests client/tests/test_linux_pygame_smoke.py`.
The first wheel probe assumed literal YAML `parameters:` text, but the shipped
manifests use supported JSON-form YAML. Correcting the disposable probe to use
`yaml.safe_load` produced the passing clean-root run below. Neither incident
required or caused a product change.

## C. CI contract

Inspected `.github/workflows/ci.yml`, `linux-gui-smoke.yml` and
`linux-package.yml` from the candidate, not inferred from architecture prose.

- Required main CI runs Linux core tests on Python 3.10–3.14, installs only
  core/dev dependencies, runs Ruff, checks launcher import isolation, and
  excludes GUI tests. Python 3.15-dev is a separate non-blocking warning job.
- Linux wheel CI builds on Python 3.10 and runs `tools/check_wheel.py`.
- Windows CI runs process containment/worker/supervision and NTFS
  revision-capture subsets on Python 3.10, then the canonical four-executable
  build and its embedded startup/scaffolding smokes.
- Optional GUI CI runs Pygame X11 smokes on Python 3.10/3.14 and the root
  Designer tests on Python 3.10. Its push trigger is `main`, not
  `v5-research`; qualifying evidence needs the appropriate PR or manual run.
- Linux packaged CI pins Ubuntu 24.04/Python 3.14, builds the four frozen
  applications, checks native dependencies, CLI/scaffolding, a fixed Quorum
  match, headless replay, contamination and archive/GLIBC metadata. Automatic
  pushes are scoped to `v4-rc2-development`; other branches need manual action.

Gaps: main CI does not run mypy; its wheel check does not perform this clean
wheel parameter/author workflow; existing frozen creation smokes omit
`--api-version 2` and therefore exercise only the passing historical template.
The 17 passing packaging-spec tests also missed the absent API-v2 resources.
The standalone Designer spec contains the same template omission, and Linux
uses the shared specs; those effects are inferred from source, not separately
executed failures. These are concrete remediation/qualification coverage gaps.

No remote CI status was queried, and no green candidate CI is claimed. All
required CI must be green for the eventual replacement SHA, with separate
mypy and the missing Alpha-critical packaged checks recorded.

## D. Python artifacts

Normal setuptools build frontend, from the clean Git-export directory:

```powershell
& 'D:\Projects\BATTLE2\.venv\Scripts\python.exe' -m build --no-isolation --outdir 'D:\Projects\BATTLE2\dist\phase-f-0dde69c-20260909\python'
```

The frontend built the sdist and then built the wheel from that sdist.
Build log interval: **2026-09-09 13:52:32–13:52:42 UTC**. No source edits or
dependency upgrades were needed. Setuptools printed license-configuration
deprecation notices; the build succeeded.

`tools/check_wheel.py` passed. Wheel: 204 members; sdist: 295 members.
All **78 engine data assets** compared byte-identically between wheel and
sdist, including the four V5 starters, schema/preset manifests, support data
and both API-v2 scaffold templates. No compiled bytecode/cache was found in
either archive, and no research directory was installed by the wheel.
README metadata and license content follow the existing package configuration;
repository authoring guides are not newly added as installed package data.

A second independent rebuild was not performed before the stop. No
bit-for-bit reproducibility claim is made.

## E. Clean-install package qualification

A fresh non-editable venv installed only the wheel and its declared PyYAML
dependency. The probe ran via that interpreter's `-I` mode, removed
`PYTHONPATH`, used a separate working/data directory, and proved engine,
client and app imports came from that venv's `Lib/site-packages`.

The **15-command** successful control covered version, catalog, all six V4
and four V5 starters, schema/preset discovery, stable-V4 execution with an
omitted ruleset, preset delivery, explicit override precedence, rejection of
`attacker_reach=9` before successful artifacts, replay generation/headless
reading, an identical-seed rerun, API-v1 compatibility, and API-v2 authoring.

`far_sighted` recorded `attacker_reach=32`; an explicit override recorded 24
and changed match identity. Identical preset/seed reruns produced:

```text
match_829bcaa2dc35b8a5bbc6ace3
result_f8319dc7706483b950592c1f
```

The installed wheel contained neither PySide6 nor Pygame. Evidence:
`build/phase-f-0dde69c-20260909/wheel-probe-complete/{imports,commands,qualification}.json`.
This establishes the executed headless workflows, not the full packaged GUI
first-user story. Separate sdist installation was not run before the stop.

## F. Windows executable

Built only the unified executable to establish the suspected omission, using
the unchanged canonical spec and the same PyInstaller command structure as
`tools/build_win.ps1`, with fresh isolated work/dist paths. The full four-app
wrapper was not run; its dependency/cleanup and embedded smoke steps are not
claimed as completed.

```powershell
# Working directory: build/phase-f-0dde69c-20260909/source
& 'D:\Projects\BATTLE2\.venv\Scripts\python.exe' -m PyInstaller --noconfirm --clean --workpath 'D:\Projects\BATTLE2\build\phase-f-0dde69c-20260909\pyinstaller' --distpath 'D:\Projects\BATTLE2\dist\phase-f-0dde69c-20260909\windows' tools\bytefray.spec
```

Build log interval: **2026-09-09 13:53:20–13:53:55 UTC**. Build succeeded.
The onedir payload has 282 files totaling 132,962,649 bytes. Its full
path/size/SHA-256 inventory is
`build/phase-f-0dde69c-20260909/frozen-payload-manifest.json` (manifest SHA-256
`25f6ce34caae239ad36aa0551695ddc649228d56a6702a06013bbb968f83a14c`).
The executable is not independently portable without that adjacent payload.

### F1. Confirmed publication blocker

Run the generated executable with `BYTEFRAY_ROOT` pointing to a fresh test
directory and `PYTHONPATH` removed:

```powershell
$env:BYTEFRAY_ROOT = 'D:\Projects\BATTLE2\build\phase-f-0dde69c-20260909\frozen-probe\data'
$phaseFExe = 'D:\Projects\BATTLE2\dist\phase-f-0dde69c-20260909\windows\bytefray\bytefray.exe'
& $phaseFExe --version
& $phaseFExe agents create v1_control
& $phaseFExe agents create v2_blank --api-version 2
& $phaseFExe agents create v2_annotated --api-version 2 --template annotated
```

| Control | Exit | Result |
| --- | ---: | --- |
| Frozen `--version` | 0 | `5.0.0a1` |
| Frozen API-v1 creation | 0 | Both scaffold files created |
| Frozen API-v2 blank creation | 2 | `ERROR: Agent template resource directory not found` for `agent_template_v2` |
| Frozen API-v2 annotated creation | 2 | Same error for `agent_template_v2_annotated` |
| Clean installed wheel API-v2 creation + validation | 0 / 0 | Valid Agent API v2 scaffold |

The actual frozen resource directory contains only `agent_template` and
`agent_template_annotated`. `agent_scaffold.py` selects the two missing
directories for API version 2, but `tools/bytefray.spec` includes neither.
Full commands and error paths are in
`build/phase-f-0dde69c-20260909/frozen-template-probe.json`.

Severity: **publication blocker** — a supported new-agent workflow fails in
the distributed application. Likely affected areas: unified and standalone
Designer resource declarations and corresponding frozen-package coverage.
The CLI-only and replay-viewer specs should be assessed according to the
commands they actually expose, not changed indiscriminately.

**CANDIDATE INVALIDATED — REMEDIATION REQUIRED.** A source/package fix requires
a new candidate SHA. Qualification stopped when the failure was confirmed;
no product source, spec, test or golden was patched.

## G. Windows installer

Inno Setup exists at the normal per-user installation path. No candidate
installer was built or installed after the confirmed executable defect.
Fresh install, installer upgrade, uninstall and installed GUI qualification
are **not completed**. No stale installer belongs in this candidate inventory.
Windows Sandbox was not installed on the host; no disposable Windows test VM
was established. No host installer registry/environment changes were made.

## H. Starter refresh

The 24 focused refresh tests passed: fresh catalog, all four pristine old
starter upgrades, customized-copy preservation, current-copy idempotence,
historical V4 preservation and reporting. The clean wheel bootstrapped the
current catalog successfully. Packaged upgrade/installer cases were not
executed before the stop. The user's real ProgramData starter directories,
including the historical customized `v5_core_defender`, were untouched.

## I. First-user workflow

Source GUI tests passed for typed controls, presets, launch rejection,
Randomize Seed, A/B/C paths, ruleset synchronization and result parameters.
Installed-wheel CLI settings reached execution and reproduced result identity.
The complete packaged GUI sequence (choose starter, preset, randomize visible
seed, launch, result view, replay and rerun) was **not completed**. Frozen
Designer startup/controls and visible replay interaction were not tested.

## J. Author workflow

Using the lifecycle, manifest, process declarations and action contract in
`docs/AGENT_API_V2.md` sections B–D/F/M, the wheel probe constructed a minimal
one-process agent with a declarative integer reach schema and `wide` preset.
It validated, ran against `v4_scout`, and recorded effective `reach=16`.
The supported `agents create --api-version 2` command also created and
validated a scaffold from the installed wheel. The frozen counterpart failed
as recorded in F1. Packaged Designer authoring was not qualified.

## K. Legacy compatibility

Source historical V4 equivalence/immutability/integration tests passed.
The clean installed wheel ran API-v1 `claimer` versus `hunter` with an unknown
free-form parameter; the historical warning-and-ignore behavior remained and
omitted ruleset resolved to `bytefray-rules-2`. Its replay opened headlessly.
The frozen API-v1 scaffold creation control succeeded. No claim is made that
all legacy packaged workflows were completed.

## L. Replay, headless and execution-boundary sanity

The replay contract and full source suite passed, including historical replay
coverage and Phase E's parameter-free/malformed-result presentation cases.
The installed wheel generated and read current v4 and API-v1/v3 replays.
Independent installed-package runs over every old fixture were not performed.
PySide6/Pygame were absent in the clean wheel venv; the executed core CLI and
headless replay commands succeeded without either.

Narrow source audit: Designer catalog/schema discovery parses manifests rather
than importing agents; YAML uses `safe_load`; presets are declarative scalar
values interpreted by the canonical parameter resolver; agent-package imports
validate archive metadata and contained paths before extraction. Development
validation retains supervised execution. Passing containment/supervision and
package tests are included in the full source run. This is regression sanity,
not a full security audit or a claim that arbitrary Python agents are securely
sandboxed. No execution-boundary remediation was made.

## M. Cross-platform qualification

WSL inspection found Ubuntu 24.04.3 LTS, x86_64, Python 3.12.3. Only environment
inspection ran: **no Linux candidate package result is claimed**. Prior
release policy includes explicit Linux package and frozen-binary checks;
Windows/source tests do not replace them. The shared frozen specs make the
missing-template finding relevant to Linux, but an actual Linux failure was
not reproduced in this phase.

No Linux checklist was created for the invalidated SHA: the next action is
remediation and a new freeze, not handoff of an allegedly qualified candidate.

## N. Artifact inventory

Every row below originates from
`0dde69c9695c8c730fe190af23f6d92783072ffd`, version `5.0.0a1`.
These are diagnostic candidate artifacts, **not approved release assets**.

| Type | Filename | Bytes | SHA-256 | Qualification status |
| --- | --- | ---: | --- | --- |
| Wheel | `bytefray-5.0.0a1-py3-none-any.whl` | 970136 | `d6aea8e205d5f05a977c8bb7297a3d062137226a69f3416f6e04057028f16013` | Contents and Windows clean headless workflows passed; overall release blocked |
| Sdist | `bytefray-5.0.0a1.tar.gz` | 947929 | `a2364e5dc6d052bd7c0917777cb27cab1fa1e4606654a7d0f6d2ad52b51144f6` | Built; wheel successfully built from it; 78 data assets equivalent; separate install not run |
| Windows unified executable | `bytefray.exe` | 4072028 | `4f1527fc5c14ca29e7a61fee3ace77e4703b8daa51ac07cc93036e949f602eda` | Build/version/API-v1 control passed; API-v2 creation **failed** |
| Windows installer | Not produced | — | — | Stopped before build |

Python artifacts are under `dist/phase-f-0dde69c-20260909/python/`; the complete
unified onedir payload is under `dist/phase-f-0dde69c-20260909/windows/bytefray/`.
Old artifacts elsewhere are excluded. Hash and command evidence is under
`build/phase-f-0dde69c-20260909/`. No second-build hash equivalence was tested.

## O. Current known limitations and Alpha story

These are distinct from the confirmed packaging defect:

| Classification | Still-applicable constraint/limitation |
| --- | --- |
| Intentional design constraint | Stable V4 local legal information; attackers are not given enemy core coordinates. Contact-centered pressure need not locate a roaming opponent's objective. |
| Known limitation | Equal-speed blind self-play/contact edge cases remain in the educational starter family. |
| Known limitation | `MatchContextV2` contains an unhashable immutable mapping; no documented hashability dependency was found in the phase record/source coverage. |
| Intentional preservation policy | Customized stale starter copies are preserved; refresh notices are in catalog/log output, not a contextual parameter-panel notice. |
| Deferred feature | Replay-history browser/search and 4+ entrant Designer work. |

The candidate's user-visible Alpha story is stable V4 mechanics, four additive
educational V5 starters, the API-v2 guide, schema parameters/presets, typed
Designer controls, explicit Randomize Seed, safe refresh and effective-result
parameter display. The current changelog does not yet tell that story. No
release-note draft was added because the candidate did not otherwise qualify.
Historical research findings remain research records, not proposed marketing
copy. No `bytefray-rules-5` product ruleset was introduced.

## P. Publication blockers and final health

Confirmed candidate defect: missing API-v2 scaffold resources in the frozen
unified executable. This alone blocks publication and requires a replacement
source SHA. Outstanding gates also include the rest of packaged GUI/first-user
qualification, standalone executable builds, installer lifecycle, separate
sdist install, Linux qualification and exact replacement-SHA CI evidence.
Their absence is not asserted to be another demonstrated product defect.

The only tracked-scope addition is this Phase F report. Ignored additions are
the source export, build scratch, test logs/XML, disposable probe script,
isolated environments/data and the three artifacts inventoried above.
No existing source, release document or real installed starter was edited.

Final checks: HEAD and local `origin/v5-research` unchanged; only this report
untracked; tracked diff/stat and `diff --check` empty. Index remains 93,148
bytes with the same recorded modification time; `index.lock` absent. No
prohibited Git mutation command, staging, commit, tag, push or publication
action ran. Read-only `git archive` wrote only an ignored build input. No
detached/background process was launched; spawned test/application children
were awaited. All task-created execution sessions terminated. Final process
inspection found no Git, Python, PyInstaller, ISCC or Bytefray processes.

## Q. Publication verdict

**ALPHA 1 PUBLICATION BLOCKED — REMEDIATION REQUIRED**

## R. Exact next action

Open a narrowly scoped remediation phase for the missing frozen API-v2
template resources and their qualification coverage, producing a new candidate
SHA for complete Phase F requalification.
