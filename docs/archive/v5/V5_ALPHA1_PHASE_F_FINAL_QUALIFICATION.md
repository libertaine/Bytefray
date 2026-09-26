# Bytefray V5 Alpha 1 — Phase F Final Qualification

> **Publication update:** [Bytefray 5.0.0 Alpha 1](https://github.com/libertaine/Bytefray/releases/tag/b5.0.0-alpha1)
> was published as a prerelease on 2026-09-10 UTC (2026-09-09 local time).
> Sections A–W and the end-of-run safety record below retain the original
> qualification evidence and its pre-publication status. The publication
> addendum at the end records the subsequent authorized publication.

## Verdict

    ALPHA 1 PUBLICATION GATE SATISFIED — READY TO PUBLISH

The immutable post-F3 candidate passed source, exact-SHA CI, Windows frozen
build, wheel, separate-sdist, manually elevated installer/installed-product,
and explicit Linux wheel/sdist qualification. The original automated
installer attempt remains recorded in section L: UAC could not be crossed by
the VS Code Codex process, so the continuation used the required manual
elevated handoff and independently verified the resulting installation.

No product or artifact defect and no remaining publication blocker were
established. **PUBLICATION NOT PERFORMED.**

## A. Candidate identity

- Branch: `v5-research`
- Frozen candidate SHA: `28a10b8f8fd47bf32ec9281dcc21b0645276962c`
- `origin/v5-research`: `28a10b8f8fd47bf32ec9281dcc21b0645276962c`
- HEAD equals `origin/v5-research`: YES
- Product version: `5.0.0a1`
- Candidate product source remained frozen: YES. The only tracked change made
  by qualification is this report, which is explicitly outside the frozen
  candidate identity.
- Host: Microsoft Windows NT `10.0.26120.0`, AMD64, PowerShell 7
- Development interpreter: CPython `3.13.14`; pip `26.2.1`
- Compatibility interpreter: CPython `3.11.9` in a disposable environment
- Build tools: build `1.6.0`, setuptools `84.0.0`, wheel `0.48.0`, PyInstaller
  `6.22.2`, PySide6 `6.11.2`, pygame-ce `2.5.8`, Inno Setup `6.7.3`

### Starting Git/index health

- `git --no-optional-locks status --short --untracked-files=all`: clean,
  exit `0`, with complete untracked inspection and no warning
- `git --no-optional-locks diff --check`: clean, exit `0`
- `.git/index.lock`: absent
- `.git/index`: `95,507` bytes; last write `2026-09-09 16:29:02` local time
- Candidate freeze precondition: PASS

### Continuation identity checks

- Before the manual installer continuation and again before the Linux-only final
  continuation, HEAD and `origin/v5-research` were exactly
  `28a10b8f8fd47bf32ec9281dcc21b0645276962c`.
- The only tracked change was this report; `diff --check` passed and
  `.git/index.lock` was absent.
- Wheel, sdist, and installer hashes were re-established before their
  respective handoffs. No candidate artifact was rebuilt or substituted.

The Win32 CIM process query was denied by the host. `Get-Process` was used as
the read-only fallback and remained sufficient to distinguish awaited task
processes from unrelated processes.

## B. Remediation provenance

All three remediation commits are ancestors of the frozen candidate:

| Round | Commit | Subject | Present |
|---|---|---|---|
| F1 | `45ccc3462cf95686846bd6c4a2f5af31869c0cdb` | `fix(packaging): include API v2 scaffold resources` | YES |
| F2 | `c28079895ff6ba7faf84620e3c8f26ab4939a82a` | `fix(packaging): exclude bytecode from frozen artifacts` | YES |
| F3 | `bfc8097ec61eb098efdc787fa0a2a8d642974d16` | `fix(ci): harden cross-platform alpha qualification` | YES |

The original blocked Phase F, F1, and F2 artifacts remain invalidated
non-publication artifacts. None of their hashes or qualification results was
reused.

## C. Source qualification

| Gate | Current-candidate result |
|---|---|
| F3 separator/path regression | `57 passed, 1 skipped`; the skip was the expected artifact-dependent check before an executable was supplied |
| No-Git-history refresh fixture | `24 passed`; ran from a directory where `git rev-parse` failed with exit `128` as expected |
| CPython 3.11 compatibility | PASS on `3.11.9`; both affected dataclass defaults constructed independently, produced fresh mappings, and rejected mutation |
| Current Python compatibility | PASS on CPython `3.13.14` with the same probe |
| Release-focused source set | `592 passed, 7 skipped` in `38.04s`; skips were artifact-dependent checks before the frozen artifact existed |
| Focused Designer/lifecycle set | `55 passed` in `3.98s` with Qt offscreen and SDL dummy drivers |
| Full headless suite | `3355 passed, 21 skipped, 3 deselected` in `379.65s`; no failures, errors, or flakes observed |
| Complete GUI/app selection | `340 passed, 6 deselected` in `48.33s`; no failures, errors, or skips |
| Ruff | PASS — `All checks passed!` |
| mypy engine | PASS — 107 source files |
| mypy client | PASS — 16 source files |
| mypy packaging helper | PASS — `tools/packaging_data.py` |

## D. Stable gameplay

- Stable V4 equivalence: PASS as part of the 592-test focused gate, including
  `test_v4_stable_ruleset_equivalence.py`.
- Stable dispatch/default: PASS; API-v2 omitted-ruleset matches selected the
  distinct permanent identity `bytefray-rules-4`.
- V4 placement/scheduler semantics: PASS in focused and full suites.
- R1/R2 production hygiene: PASS; exact production searches across
  `engine/src`, `client/src`, `app`, and `agents` found no R1/R2 experiment
  identity residue.
- V4 starters: all six V4 agents were discoverable from the clean wheel and
  frozen package; stable matches completed.
- V5 starters: all four expected starters were discovered and exercised by
  source/package coverage.
- Parameters/presets: PASS. `v5_region_attacker` exposed
  `attacker_reach` and `standard`/`far_sighted`; preset plus explicit override
  resolved to `24`, reached process execution, and was recorded in result
  metadata. Value `9` was rejected below the declared minimum `10`.
- Determinism: two wheel-installed matches with identical seed/settings
  produced byte-identical replay files with SHA-256
  `AA3FD3C4893DA82D609804B6224D165F62ACF08A857CB3C3466C9016E2612032`.

## E. CI

Exact-candidate GitHub Actions run:
`https://github.com/libertaine/Bytefray/actions/runs/34401313185`

- Event/status/conclusion: `push` / `completed` / `success`
- Head SHA: `28a10b8f8fd47bf32ec9281dcc21b0645276962c`
- Required Linux core matrix: Python `3.10`, `3.11`, `3.12`, `3.13`, and
  `3.14` — all SUCCESS
- Next-Python informational job: `3.15-dev` — SUCCESS
- Linux wheel job: SUCCESS
- Windows executable job: SUCCESS, including actual `build_win.ps1`
- Ruff: SUCCESS in the Linux matrix
- Core tests, import isolation, wheel checks, Windows containment/revision
  checks, packaging tests, and shallow-checkout-sensitive tests: SUCCESS
- No mypy job is configured in `ci.yml`; the required local engine/client
  mypy invocations both passed in section C.
- Optional Linux GUI and Linux pMARS workflows were not required by this push
  and are not represented as having run.

## F. Windows build orchestration

The actual release command completed successfully:

```powershell
& 'C:\Program Files\PowerShell\7\pwsh.exe' -NoProfile -File tools\build_win.ps1
```

It rebuilt all four PyInstaller onedir targets, ran the packaging guard, ran
the unified and standalone Designer startup smokes with automated exit, and
ran API-v1 plus both API-v2 scaffold smokes. Final result: `[build] Success`.

## G. Frozen artifacts

| Artifact | Bytes | SHA-256 | Result |
|---|---:|---|---|
| `dist/windows/bytefray/bytefray.exe` | 4,072,163 | `932C982B2C727422DFF61A1D343D56A94099B661A6D8E82D6482335DD3DBCE12` | QUALIFIED |
| `dist/windows/bytefray-cli/bytefray-cli.exe` | 2,767,035 | `43BE230CEEBaf18E3D864E55A2B73E784D154051A1B2448B5690CA750E36CCED` | QUALIFIED |
| `dist/windows/bytefray-agent-designer/bytefray-agent-designer.exe` | 4,065,842 | `9B91FED22D18C3492C9449AE4A278E71FE00DEEFC490DCBB7825C6912A356520` | QUALIFIED |
| `dist/windows/bytefray-replay-viewer/bytefray-replay-viewer.exe` | 3,825,996 | `D7B1F2B2EC8E1E8ABF76493D1D8E0AC72C8CAD980570265A6C0D0774EA94431B` | QUALIFIED |

Independent recursive inspection found zero `__pycache__` directories, zero
`.pyc`, and zero `.pyo` files in every payload. Expected native `.pyd` files
were correctly retained. The unified and CLI payloads contained the licensed
pMARS Windows resource; all applicable targets contained their expected
branding, starter, template, and replay resources. No runtime `agents/`
directory was mistakenly bundled beside an executable.

## H. F1 regression

- Frozen-specific test gate after build: `74 passed` in `3.93s`.
- API-v1 blank scaffold: creation, validation, and execution PASS.
- API-v2 blank scaffold: creation, validation, and execution PASS.
- API-v2 annotated scaffold: creation, validation, and execution PASS.
- Frozen version: `5.0.0a1`.
- The isolated working/data root had `PYTHONPATH` removed and was outside the
  checkout. Source-tree fallback was therefore excluded: YES.

## I. F2/F3 regression

- Canonical frozen-payload bytecode guard: PASS.
- Negative control: PASS. A disposable contaminated payload containing
  `_internal/pkg/__pycache__/bad.pyc` caused the guard test to fail exactly as
  required (`1 failed`, exit `1`); publication payloads were untouched.
- Slash/backslash and `.pyd` classification coverage: PASS (`57 passed,
  1 expected pre-artifact skip`).
- F3 no-history and Python compatibility gates: PASS as detailed in section C.

## J. Wheel

- Artifact: `bytefray-5.0.0a1-py3-none-any.whl`
- Bytes: `970,684`
- SHA-256: `BB8B6AD47D3C8B481415A72DD7514FD13159F6417AB71169689B9A2302BC252A`
- Candidate SHA: `28a10b8f8fd47bf32ec9281dcc21b0645276962c`
- Metadata version: `5.0.0a1`; members: `204`
- Canonical `tools/check_wheel.py`: PASS
- Independent contents: all four V5 starters, schema manifests, parameter
  data, both API-v2 templates, no cache/bytecode, and no research-only product
  agents.
- Clean non-editable install: PASS. Imports resolved from the disposable
  environment's `site-packages`, not the checkout.
- Installed workflows: version, agent listing, schema/presets, stable match,
  override, invalid rejection, deterministic replay, API-v1 scaffold, both
  API-v2 scaffolds/validation/execution, result metadata, and headless replay
  read all passed.
- Headless environment installed only Bytefray, PyYAML, and pip; neither
  PySide6 nor pygame was discoverable.

## K. Sdist

- Artifact: `bytefray-5.0.0a1.tar.gz`
- Bytes: `948,360`
- SHA-256: `03AAF95EFA6A87409789D10EEE5D91626B40A6561BE637CD42968B9818E9917A`
- Candidate SHA: `28a10b8f8fd47bf32ec9281dcc21b0645276962c`
- Metadata version: `5.0.0a1`; members: `295`
- Contents: all critical starters/manifests/templates present; no packaged
  cache/bytecode or research-only product agents.
- Separate environment built a wheel from this sdist and installed it: PASS.
  Version, starters, schema, API-v1, both API-v2 templates, both API-v2
  validations, stable V4 match, and replay read all passed from `site-packages`.
- Reproducibility investigation: the sdist-built wheel had the same 204 member
  names and byte-identical contents as the canonical wheel. Six ZIP timestamps
  differed, so the outer wheel hashes differed. Bit-for-bit reproducibility is
  not claimed.

## L. Installer

- Artifact: `Bytefray-Setup-5.0.0a1.exe`
- Bytes: `100,860,042`
- SHA-256: `DFAA25609405CA170BED0DF7A6E684FC72F316B91FD846837F79909D3B07379F`
- Product version: `5.0.0a1`
- Candidate SHA: `28a10b8f8fd47bf32ec9281dcc21b0645276962c`
- Inno Setup: `6.7.3`
- Build: PASS from the actual `tools/installer.iss` release path.
- Original automated attempt: environment/tooling blocked. The host shell was
  not administrative; the awaited `Start-Process -Verb RunAs` request returned
  `The operation was canceled by the user`. This was a UAC boundary, not a
  product defect, and created no partial installation.
- Manual elevated handoff: USED. Immediately before handoff the installer hash
  matched the canonical value above. The user ran the exact silent controlled-
  root command in a separate Administrator PowerShell and reported exit `0`, no
  dialog/error, and the expected Bytefray Start Menu group.
- Fresh install: PASS. The installation log ended `Installation process
  succeeded`; registry state reported Bytefray `5.0.0a1`, the controlled app
  root, and the controlled `BYTEFRAY_ROOT`. All four executables and the
  uninstaller were present; no partial/failed state was found.
- Installed payload provenance: PASS. Recursive file/hash comparison against
  the already-qualified frozen trees found `286/65/287/92` source files for
  unified/CLI/Designer/Replay Viewer respectively, with zero missing, extra,
  or different files. Installed README/LICENSE bytes also matched.
- Fresh installed workflow: PASS. Installed version was `5.0.0a1`; all six V4
  and four V5 starters, V5 schemas/presets, stable matches, deterministic
  replay, result metadata, and headless replay processing passed with the
  checkout removed from `PYTHONPATH`.
- Pristine historical upgrade: PASS using only the committed Phase C fixture.
  All four V5 starters upgraded from `1.0.0` schema-less bytes to current
  `1.1.0` bundled bytes, with no duplicate IDs; the second refresh rewrote
  zero files.
- Customized historical upgrade: PASS in a separate controlled catalog. A
  customized `v5_region_attacker/agent.py` and customized
  `v5_dual_team/agent.yaml` were byte-preserved; the permitted missing dual
  source file was restored from the bundle without overwriting customization.
  The resulting catalog remained discoverable; the second refresh rewrote
  zero files.
- Installer starter-refresh idempotence: PASS for current, pristine-upgraded,
  and customized-preserved states. The user's real customized
  `v5_core_defender` was not used.

## M. Designer

- Source/UI service qualification: PASS (`55 passed` focused; covered again in
  `340 passed` complete GUI/app selection).
- Schema-generated typed controls, presets, explicit overrides, Randomize
  Seed, A/B/C entrant paths, and ruleset synchronization: PASS in source GUI
  automation.
- Unified and standalone frozen Designer startup smokes: PASS with automated
  exit during `build_win.ps1`.
- Installed standalone/unified startup smokes: PASS with deterministic exit.
- Installed-package interactive workflow: PASS by manual user operation of the
  installed standalone Designer. `v5_region_attacker`, `far_sighted`, stable
  Ruleset V4, and Randomize Seed produced concrete seed `556385` and effective
  `attacker_reach=32`; both matches completed and Replay Viewer opened without
  error.
- Independent artifact verification found both runs completed at tick `12`
  with identical match ID `match_c30d3179b8d281f0cae034bb`, result ID
  `result_bba81dcd5f957527977d9e4a`, replay/result/summary bytes, winner A, and
  A's recorded process reach `32`. Only non-semantic diagnostic trace timing
  differed.

## N. First-user workflow

PASS. The installed product exposed the schema and `far_sighted` preset,
Randomize Seed produced visible seed `556385`, the effective parameter reached
execution/result presentation, Replay Viewer opened the generated replay, and
the same seed/settings reproduced the same semantic and canonical artifacts.

## O. Author workflow

PASS. Frozen, clean-wheel, separate-sdist, and installed-product paths created,
validated, loaded, and executed the API-v1 scaffold and both API-v2 blank and
annotated scaffolds. The installed API-v2 blank scaffold was then modified to
the documented typed parameter schema (`probe_reach`, default `1`, range
`1`-`8`, preset `wide=4`). Installed discovery and Designer startup accepted
the schema; a stable match with preset plus explicit override recorded and
executed reach `3`.

## P. Legacy compatibility

- API-v1 scaffold creation/validation/execution: PASS in frozen, wheel, and
  sdist workflows.
- Omitted-ruleset API-v1 execution selected `bytefray-rules-2`: PASS.
- V4 starters and stable-v4 execution: PASS.
- Historical replay/result compatibility: PASS in the focused and full source
  suites and from installed-product paths. Installed headless replay parsed
  representative schema-v1 and schema-v2 historical streams, plus the current
  schema-v4 stream. Current results with parameter metadata and compatible
  entrants without parameter metadata were accepted.

## Q. Headless

- Clean wheel without GUI/replay extras: PASS.
- `bytefray --version`, `bytefray agents`, matches, and headless replay: PASS.
- PySide6 discoverable/imported: NO.
- pygame discoverable/imported: NO.
- Installed security/sandbox sanity: PASS. Catalog/schema discovery did not
  execute an agent module with a top-level marker; a non-returning `act()` was
  terminated by the supervised action process with `agent_action_timeout` and
  left no worker; a traversal-shaped scaffold ID was rejected with no escaped
  path. Parameter schema/preset data remained declarative.

## R. Linux qualification

- Environment: Ubuntu `24.04.3 LTS` (Noble), WSL2, kernel
  `6.6.87.2-microsoft-standard-WSL2`, x86_64; CPython `3.12.3`; pip `24.0`;
  Git `2.43.0`. Current V5 records explicitly accept WSL as a real Linux host,
  and this distro matches the documented Ubuntu 24.04 baseline. This evidence
  is limited to wheel/sdist packaging and makes no self-contained Linux frozen-
  archive claim.
- Exact wheel Linux SHA-256:
  `BB8B6AD47D3C8B481415A72DD7514FD13159F6417AB71169689B9A2302BC252A`.
  Windows hash == Linux hash: YES.
- Wheel clean install: PASS in a newly-created `/var/tmp` venv with
  `PYTHONPATH` unset. Version reported `5.0.0a1`; imports resolved from that
  venv's `site-packages`, not the checkout.
- Wheel catalog/schema: PASS. Exactly all six V4 and four V5 starter IDs were
  present. `v5_region_attacker` exposed `attacker_reach` and presets
  `standard`/`far_sighted` from wheel-installed resources.
- Wheel author workflow: PASS. API-v1, API-v2 blank, and API-v2 annotated
  scaffolds were created from installed resources, validated with dry-run
  actions, and each executed in a real match.
- Wheel parameter workflow: PASS. `far_sighted` recorded and executed
  `attacker_reach=32`; explicit override recorded and executed `24`;
  `attacker_reach=9` was rejected with exit `1` and no replay artifact.
- Wheel stable/headless/reproducibility: PASS. Two stable V4 runs produced
  byte-identical replays, each SHA-256
  `BCB83A118F16DA4442B20EDC34D64A4D71D94C17D8316FC9197C7CBA984B7597`,
  and the installed headless renderer parsed the replay. Two parameterized
  runs produced identical match ID `match_3efd1075ae8fd65894330fa4`, result ID
  `result_5d158cb5869a156aaf640f84`, byte-identical results/replays, and replay
  SHA-256 `5215C3F39D75F57114562328EBEB86F526479384CCD6A9B571D7482B86D5792B`.
- Wheel headless boundary: PASS. The clean environment contained only
  Bytefray and PyYAML as product/runtime distributions; `find_spec` returned
  `None` for both PySide6 and pygame while version, catalog, matches, and
  headless replay succeeded. PySide6 required = NO; pygame required = NO.
- Exact sdist Linux SHA-256:
  `03AAF95EFA6A87409789D10EEE5D91626B40A6561BE637CD42968B9818E9917A`.
  Windows hash == Linux hash: YES.
- Separate sdist build/install: PASS. A second newly-created venv installed
  from the exact `.tar.gz`; pip successfully built its ephemeral install wheel,
  installed it, and the exercised module resolved from that venv's
  `site-packages`. The canonical wheel was not substituted.
- Sdist catalog/schema/authoring: PASS. All six V4 and four V5 starters,
  parameter schema/presets, API-v1 scaffold, API-v2 blank scaffold, and API-v2
  annotated scaffold passed; all three scaffolds validated and executed.
- Sdist parameter/stable/headless: PASS. Preset reach `32`, explicit reach
  `24`, invalid-value rejection, deterministic stable V4 match, and headless
  replay all reproduced the wheel-environment results. PySide6 and pygame were
  absent and not required.
- F3 Linux sanity: PASS. The focused bytecode classifier module completed
  `57 passed, 1 skipped`, covering both `/` and `\` spellings and retaining
  `.pyd` as an allowed native extension. In a minimal tree with no reachable
  `.git`, `git rev-parse` exited `128` and all `24` historical starter-refresh
  tests passed from the committed fixture.
- Package-content hygiene: PASS by direct archive inspection. The wheel had
  `204` members and the sdist `295`; neither archive contained `__pycache__`,
  `.pyc`, `.pyo`, or backslash-spelled archive members. Runtime venv caches
  were not misclassified as publication-artifact contents.

Linux wheel/sdist packaged qualification is complete. **PUBLICATION NOT
PERFORMED.**

## S. Artifact inventory

Every artifact below is sourced from candidate
`28a10b8f8fd47bf32ec9281dcc21b0645276962c`.

| Type | Filename | Version | Bytes | SHA-256 | Platform | Qualification |
|---|---|---|---:|---|---|---|
| Wheel | `bytefray-5.0.0a1-py3-none-any.whl` | `5.0.0a1` | 970,684 | `BB8B6AD47D3C8B481415A72DD7514FD13159F6417AB71169689B9A2302BC252A` | Any/Python | Windows and Linux clean-install PASS |
| Sdist | `bytefray-5.0.0a1.tar.gz` | `5.0.0a1` | 948,360 | `03AAF95EFA6A87409789D10EEE5D91626B40A6561BE637CD42968B9818E9917A` | Source | Windows and Linux separate-build/install PASS |
| Unified frozen app | `bytefray.exe` | `5.0.0a1` | 4,072,163 | `932C982B2C727422DFF61A1D343D56A94099B661A6D8E82D6482335DD3DBCE12` | Windows AMD64 | PASS |
| Frozen CLI | `bytefray-cli.exe` | `5.0.0a1` | 2,767,035 | `43BE230CEEBaf18E3D864E55A2B73E784D154051A1B2448B5690CA750E36CCED` | Windows AMD64 | PASS |
| Agent Designer | `bytefray-agent-designer.exe` | `5.0.0a1` | 4,065,842 | `9B91FED22D18C3492C9449AE4A278E71FE00DEEFC490DCBB7825C6912A356520` | Windows AMD64 | Frozen and installed workflow PASS |
| Replay viewer | `bytefray-replay-viewer.exe` | `5.0.0a1` | 3,825,996 | `D7B1F2B2EC8E1E8ABF76493D1D8E0AC72C8CAD980570265A6C0D0774EA94431B` | Windows AMD64 | Frozen and installed workflow PASS |
| Installer | `Bytefray-Setup-5.0.0a1.exe` | `5.0.0a1` | 100,860,042 | `DFAA25609405CA170BED0DF7A6E684FC72F316B91FD846837F79909D3B07379F` | Windows AMD64 | Build/install/installed lifecycle PASS |

The Git-archive build input was taken directly from the frozen SHA and had
SHA-256 `0F3E7BC55A0B4AAAEA7B9A33840F3BD188849752E4039ED24AC31117B95018AE`.
It is provenance evidence, not a publication artifact.

## T. Known limitations

Only limitations still applicable to the candidate are retained:

- Intentional stable-V4 information constraint: agents receive local legal
  information and are not directly told an enemy core location.
- Educational starter edge case: blind-contact/equal-speed self-play cases can
  exist.
- `MatchContextV2` is unhashable because it carries an immutable mapping. The
  authoring contract expressly disallows dependence on object hash/identity,
  and no product/test use was found.
- Customized historical starter copies are preserved rather than overwritten;
  refresh reports the preservation.
- Replay history/search, 4+ entrant Designer layouts, and larger automated
  evolution/mutation systems remain deferred.

The resolved F1/F2/F3 defects are not listed as current limitations.

## U. Publication blockers

None. Windows/source/installed-product qualification is complete, the exact-
SHA CI run is green, and explicit Linux wheel/sdist qualification passed.
Candidate remediation required: NO. New candidate SHA required: NO.
**PUBLICATION NOT PERFORMED.**

## V. Final verdict

    ALPHA 1 PUBLICATION GATE SATISFIED — READY TO PUBLISH

## W. Exact next action

Obtain explicit publication authorization, then run the separate Alpha 1
publication procedure against candidate
`28a10b8f8fd47bf32ec9281dcc21b0645276962c` using only the qualified artifacts
and hashes in section S; do not rebuild or substitute them.

## End-of-run safety record

- Product source changed: NO
- Expected tracked file changed: this qualification report only
- Release-note draft changed: NO; this final continuation was Linux
  qualification/report completion only
- Ignored outputs retained: qualified frozen trees, wheel, sdist, installer,
  exported source, controlled installed-product evidence, and qualification
  helpers under `build/`/`dist/`
- External disposable Linux venv/data/work roots: removed after successful
  qualification
- Git mutation command run: NO
- Publication action run: NO
- Background/detached process launched by Codex: NO; every child was awaited
- All task-created processes terminated: YES; final checks returned
  `WINDOWS_TASK_PROCESS_MATCHES=NONE` and `WSL_TASK_PROCESS_MATCHES=NONE`
- Final Git status: only
  `M docs/research/v5/V5_ALPHA1_PHASE_F_FINAL_QUALIFICATION.md`
- Final `diff --stat`: one expected report, 371 insertions and 150 deletions
- Final `diff --check`: PASS, exit `0`
- Final HEAD and `origin/v5-research`: both
  `28a10b8f8fd47bf32ec9281dcc21b0645276962c`
- Final `.git/index`: `95,507` bytes; last write unchanged at
  `2026-09-09 16:29:02` local time
- Final `.git/index.lock`: absent

## Publication addendum — 2026-09-10 UTC

    BYTEFRAY 5.0.0 ALPHA 1 PUBLISHED

Publication was explicitly authorized in a separate procedure after Phase F.
The qualification report had already been committed as
`a22446906c5d2fbd616e86a0c616743934ac814e`; the initial publication checkout
was clean and local/remote `v5-research` both pointed to that documentation
descendant. The qualified source identity remained unchanged.

### Release identity

- Qualified source and annotated tag target:
  `28a10b8f8fd47bf32ec9281dcc21b0645276962c`
- Product version at that exact commit: `5.0.0a1`
- Tag: `b5.0.0-alpha1`
- Annotated tag object: `0fe39722baec14fb09d0b36c84e1daded873e340`
- Tag annotation and release title: `Bytefray 5.0.0 Alpha 1`
- GitHub repository: `libertaine/Bytefray`
- Release classification: prerelease YES; draft NO
- Published at: `2026-09-10T03:06:57Z`
- Verified URL: <https://github.com/libertaine/Bytefray/releases/tag/b5.0.0-alpha1>
- Stable gameplay remains `bytefray-rules-4`; no Ruleset v5 was introduced.

### Exact publication inputs

All paths are relative to `D:\Projects\BATTLE2`. The bytes and full SHA-256
values in section S remain the canonical inventory; every value was recomputed
and matched immediately before upload.

| Asset | Qualified local path |
|---|---|
| `bytefray-5.0.0a1-py3-none-any.whl` | `dist/phase-f-28a10b8-20260909/python/bytefray-5.0.0a1-py3-none-any.whl` |
| `bytefray-5.0.0a1.tar.gz` | `dist/phase-f-28a10b8-20260909/python/bytefray-5.0.0a1.tar.gz` |
| `bytefray.exe` | `dist/windows/bytefray/bytefray.exe` |
| `bytefray-cli.exe` | `dist/windows/bytefray-cli/bytefray-cli.exe` |
| `bytefray-agent-designer.exe` | `dist/windows/bytefray-agent-designer/bytefray-agent-designer.exe` |
| `bytefray-replay-viewer.exe` | `dist/windows/bytefray-replay-viewer/bytefray-replay-viewer.exe` |
| `Bytefray-Setup-5.0.0a1.exe` | `dist/installer/Bytefray-Setup-5.0.0a1.exe` |

Exactly these seven assets were attached. No ZIP, checksum-file asset,
research report, or proof-only build was added. Checksums are included in the
release notes. GitHub's automatic source archive links are distinct from the
seven uploaded assets and the qualified Python sdist.

### Independent publication verification

- GitHub release page: HTTP `200`.
- GitHub release metadata: exact title/tag, prerelease YES, draft NO.
- Remote annotated tag was inspected through both Git and the GitHub API;
  its peeled commit and annotation matched the values above.
- Asset inventory: exactly seven expected filenames, no missing or extra
  uploaded assets; all byte sizes and GitHub SHA-256 digests matched section S.
- Every published asset was independently downloaded into
  `build/publication-b5-alpha1/downloaded/`. Recomputed SHA-256 and byte size
  matched the corresponding qualified local artifact for all seven files.
- Wheel published: YES. Sdist published: YES. Four frozen executables
  published: YES. Installer published: YES.
- The individual executable assets require their matching PyInstaller runtime
  directories/resources. Release notes and README direct Windows users to the
  installer for complete application layouts.
- No publication input was rebuilt, replaced, or substituted. Existing
  qualification results remain attributed to their original operators;
  publication verification above was performed during this publication run.

### Post-publication documentation

After publication and asset verification, README was rewritten around V5,
linked directly to the verified release, and substantially shortened. It
retains stable V4 gameplay and API-v1 compatibility facts, current authoring
and installation examples, the MIT license, and the existing support link.
This report's qualification evidence is preserved with this separate addendum.
The documentation update changes only README and this report; no product
source, version, gameplay, or release-tag target is changed.

Documentation validation performed during publication:

- README reduced from 529 to 237 lines and from 3,277 to 1,232 words.
- All 32 local Markdown/image targets resolved; the linked parameters anchor
  exists and fenced code blocks are balanced. Markdown structure was reviewed.
  No dedicated repository Markdown/link checker is configured.
- All seven README CLI examples passed against the unchanged qualified unified
  executable using an isolated working/data root: catalog, V5 match, headless
  replay, API-v2 annotated scaffold, validation, development test, and
  preset-plus-override match. The catalog command is `bytefray agents`.
- Both example matches completed under the omitted-ruleset default
  `bytefray-rules-4`; the parameterized result recorded `attacker_reach=24`.
- All seven original publication inputs were rehashed after these checks and
  still matched section S. No build or installation command was run during
  this publication procedure.
- Product tests/type checks were not rerun for this documentation-only change;
  their candidate qualification results remain recorded in section C.
