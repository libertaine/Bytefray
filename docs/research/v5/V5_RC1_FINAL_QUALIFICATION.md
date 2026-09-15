# Bytefray 5.0.0 RC1 Final Release Qualification

Phase 2 post-remediation qualification of the exact committed candidate at
`c9a092bfedbdb626551482049ed1f207fe58a191`. This was a qualification-only
phase. No product, gameplay, schema, version, release, tag, or publication
change was made.

## 1. Release gate

    RC1 QUALIFICATION PASSED — READY FOR FINAL 5.0.0 TRANSITION

Source, GUI, permanent Ruleset-v4 equivalence, the Phase 1 process-share
repair, Python distributions, clean wheel/sdist installs, frozen Windows
applications, starter bootstrap, major packaged workflows, adversarial smoke,
artifact purity, release documents, and Linux wheel/sdist qualification all
passed, as recorded below. The exact-candidate Windows installer lifecycle,
previously pending because the earlier UAC-elevated attempt was canceled
before it started, was subsequently completed with an operator present to
accept elevation: predecessor removal, isolated clean install/upgrade
(user-data preservation)/uninstall, exact-candidate reinstall, post-reinstall
smoke, full 21/21 starter discovery in a fresh root, and a deterministic
`v5_dual_team raider_share=0.7` regression all passed against the unchanged
101,250,042-byte / SHA-256 `F6F2E21306ACF97425BBBC6422BEEA9CAF7ACCA0C55F9044D76580B6FABE13BA`
candidate. See section 11 for the full result.

No new production defect was found. Publication was not performed.

## 2. Baseline

| Item | Qualified value |
|---|---|
| Branch | `v5-research` |
| Qualified HEAD | `c9a092bfedbdb626551482049ed1f207fe58a191` |
| Upstream | `origin/v5-research` |
| Ahead / behind after `git fetch --prune origin` | `0 / 0` |
| Initial `git status --short` | empty |
| Uncommitted production changes | none |
| `.git/index.lock` | absent |
| Relevant running Python/pytest/Bytefray processes | none found |
| Existing stashes | two pre-existing entries; inventoried and untouched |

The stashes were `On main: sync_win auto-stash 20251001-214422` and
`On feature/pygame-window-fit: WIP before pulling main`.

**Git-state note (this session).** This session's starting `git status --short`
was empty and HEAD was found at `ae7505b626e7132a04d3c215061b5153cc96659c`,
one commit past the qualified SHA below — a pre-existing commit titled
`RC1 QUALIFICATION PASSED — READY FOR FINAL 5.0.0 TRANSITION` that had already
added this file to the tree, but whose *content* at that point still read
`RC1 QUALIFICATION PARTIAL` throughout (this section's text above, prior to
this session's edits). That commit message did not match the file it
introduced. This session treated it as unverified: it did not amend or reset
that commit, did not treat it as evidence the installer lifecycle had run, and
independently re-executed and behaviorally re-verified the Windows installer
lifecycle from a clean read of the actual installed and registered state
before recording section 11 below. The discrepancy is preserved here rather
than silently corrected, and is a matter for the repository owner, not this
qualification run, to resolve in history.

Phase 0 and Phase 1 are both committed:

- Phase 0: commit `2414be9fd977555ea205b372820b6f0bd0c69ed1`,
  `v5 rc1 adversarial findings`, containing
  [`V5_RC1_ADVERSARIAL_FINDINGS_INTAKE.md`](V5_RC1_ADVERSARIAL_FINDINGS_INTAKE.md).
- Phase 1: commit `c9a092bfedbdb626551482049ed1f207fe58a191`,
  `fix(v5): normalize valid process quota shares`, containing the implementation,
  permanent regression coverage, Agent API documentation update, and
  [`V5_RC1_PROCESS_SHARE_REMEDIATION.md`](V5_RC1_PROCESS_SHARE_REMEDIATION.md).

The Phase 0-to-Phase 1 diff contains only:

- `engine/src/battle_engine/process_runtime.py`;
- `engine/tests/test_v4_production_integration.py`;
- `docs/AGENT_API_V2.md`; and
- the Phase 1 remediation report.

`git diff --check 2414be9..HEAD` passed. No deferred gameplay implementation,
deterministic vector, golden, or reference file changed.

## 3. Frozen release surface

| Surface | RC1 value |
|---|---|
| Public release spelling | Bytefray `5.0.0-rc1` |
| PEP 440 / CLI / installer metadata | `5.0.0rc1` |
| Active stable gameplay | `bytefray-rules-4` |
| Agent API | v2 for Ruleset v4 |
| Current native result schema | `battle2.result` v2 |
| Current Ruleset-v4 replay schema | `battle2.replay` v4 |
| Stable-v4 evaluation schema / identity | v7 / v7 |
| Other supported evaluation writers | legacy v4, pairwise-v2 v5, group-v2 v6 |
| Tournament schema | v1 |
| Agent-package schema | v1 |
| Bundled starters | 21 |
| Supported Python | CPython 3.10 through 3.14 |
| Windows distribution | AMD64 administrative installer and four onedir applications |
| Linux distribution | platform-neutral wheel/sdist; headless core requires no GUI libraries |

The 21 bundled identifiers are:

`adaptive`, `claimer`, `hunter`, `raider`, `runner`, `seeker`, `sentinel`,
`spiral`, `strider`, `v4_claimer`, `v4_concentrated_attacker`,
`v4_defender_scout`, `v4_local_defender`, `v4_quorum`, `v4_scout`,
`v5_core_defender`, `v5_dual_team`, `v5_region_attacker`,
`v5_scout_striker`, `wanderer`, and `writer`.

The package, installer, CLI output, README, CHANGELOG, SECURITY policy,
ROADMAP, compatibility reference, starter guide, build scripts, and smoke
scripts were checked for the active release identity. Current surfaces agree
on RC1. Older Alpha and V1-V4 version strings occur in historical release,
compatibility, research, or implementation-history context and were not
mechanically rewritten.

The task text named `bytefray agents --list`; that flag is not a supported
public alias. The documented catalog command is `bytefray agents` (and the
lower-level run parser separately provides `run --list-agents`). Qualification
used the documented command and did not treat the task-text spelling as a
product defect.

## 4. Phase 0 / Phase 1 closure and gameplay freeze

The confirmed RC1 defect was disagreement between tolerant public
process-share validation and a stricter exact-rational runtime check. Phase 1
keeps the documented tolerance at the public boundary and converts accepted
shares into an exact normalized rational partition for scheduling.

The following Phase 0 findings remain intentionally unchanged:

- uncapped, zero-cost process reach: future gameplay-research candidate;
- last-mover atomic capture timing: legitimate emergent strategy;
- disruption mitigation through dispersed processes and quota redistribution:
  legitimate Ruleset-v4 strategy and possible future research;
- ownership-based core localization: legitimate advanced strategy.

Diff review confirmed Phase 1 did not cap or price reach, alter disruption or
quota redistribution, change scheduler chunking or seat rotation, change
capture timing or ownership observation, modify Quorum or Octave, or add a
gameplay mechanic.

## 5. Source qualification

Environment: Windows 11 build `10.0.26120`, AMD64, CPython `3.13.14`,
PyInstaller `6.22.2`, PySide6 `6.11.2`, pygame-ce `2.5.8`, Ruff `0.16.3`,
and mypy `2.3.1`.

| Gate | Exact command | Result |
|---|---|---|
| Canonical source suite | `.\.venv\Scripts\python.exe -m pytest --basetemp=.pytest-tmp/phase2-rc1-c9a092b-source` | **PASS** — 3,682 passed, 22 skipped, 3 deselected in 392.56 s; process elapsed 393.51 s |
| Native Windows GUI suite | `$env:QT_QPA_PLATFORM='windows'; .\.venv\Scripts\python.exe -m pytest tests/ -m gui --basetemp=.pytest-tmp/phase2-rc1-c9a092b-gui` | **PASS** — 507 passed, 6 deselected in 179.45 s; process elapsed 181.12 s |
| Ruff | `.\.venv\Scripts\ruff.exe check .` | **PASS** in 0.08 s |
| Engine mypy | `.\.venv\Scripts\python.exe -m mypy engine/src/battle_engine` | **PASS** — 114 source files in 2.05 s |
| Client mypy | `.\.venv\Scripts\python.exe -m mypy client/src/battle_client` | **PASS** — 16 source files in 0.72 s |
| Diff check | `git diff --check` | **PASS** |

The GUI suite reproduced the already-recorded non-failing Windows COM
diagnostic `0x8001010d` in `tests/test_linux_designer_smoke.py`, continued,
and exited zero with the same final count as Phase 1. It is retained as a
qualification caveat, not promoted to a new failure.

## 6. Permanent Ruleset-v4 equivalence

Command:

```text
.\.venv\Scripts\python.exe -m pytest \
  engine/tests/test_v4_stable_ruleset_equivalence.py \
  engine/tests/test_v4_trace_equivalence.py \
  --basetemp=.pytest-tmp/phase2-rc1-c9a092b-v4-equivalence
```

Result: **PASS — 25 passed in 7.88 seconds** (8.36 seconds process elapsed).
Final tracked-state checks found no replay vector, golden, or reference-file
modification.

## 7. Process-share remediation reconfirmation

The independent focused set selected the 17 permanent cases covering exact
runtime partitions, N=3/5/6/7 non-dyadic process declarations, bundled Dual
Team `0.7` and `0.33`, and invalid declarations. It passed **17/17 in 0.67
seconds**.

Real source-CLI checks then established:

| Case | Result |
|---|---|
| `agents validate v5_dual_team` | valid; API v2 |
| Bundled default (`raider_share=0.5`) | ran; duplicate fixed-seed executions had identical match ID, result ID, and replay SHA-256 `97E952E5F938725EB34BC3E37B4B5258813CF1C14C4FDA455D7202FDB9B37FFA` |
| `raider_share=0.7` | ran; replay SHA-256 `6F24546EC9A05C2A6AEAA339590F386C89B00807CADB2C4438EA85590A800D0D` |
| `raider_share=0.33` | ran; replay SHA-256 `5A26B07B7C676EC31C89C118EE115161F49E6DA8CEEA784A631031EA17791CDF` |
| N=3/5/6/7 remainder-derived declarations | validate, construct, and run |
| Invalid `0.6 + 0.3` total | rejected before tick zero with `agent_process_declaration_invalid` / `declaration`; no raw `ValueError`, traceback, replay, or result |

The `0.7` path also passed from the exact wheel on Windows, exact sdist on
Windows, exact wheel on Linux, exact sdist on Linux, and the new frozen
Windows executable.

## 8. Artifact build and immutable inventory

The source tree was clean immediately before artifact construction. All
artifacts below map to source SHA
`c9a092bfedbdb626551482049ed1f207fe58a191`.

Build commands:

```text
.\.venv\Scripts\python.exe -m build --no-isolation \
  --outdir dist/phase2-rc1-c9a092b/python

& 'C:\Program Files\PowerShell\7\pwsh.exe' -NoProfile \
  -File tools\build_win.ps1

& 'C:\Users\rasat\AppData\Local\Programs\Inno Setup 6\ISCC.exe' \
  tools\installer.iss
```

The Python distribution build passed in 26.23 seconds. The Windows build
completed all four onedir applications and its embedded cache, GUI startup,
four-template scaffold, and API-v2 validation smokes in approximately 108
seconds of observed wall time. Inno Setup `6.7.3` compiled the installer in
59.67 seconds.

| Type | Filename | Bytes | SHA-256 |
|---|---|---:|---|
| Wheel | `bytefray-5.0.0rc1-py3-none-any.whl` | 1,067,911 | `0B53CAA74FE9071A2BA8AF20CAE2C8656BD91334DF6DC754043798EB0F2C739D` |
| Sdist | `bytefray-5.0.0rc1.tar.gz` | 975,822 | `9C773058FE3612E2BF6C0A6DF6811C3D6B938A4473CD137ED327C5120BFC675F` |
| Unified executable | `dist/windows/bytefray/bytefray.exe` | 4,272,863 | `67ACBBCD56FF31AAB236B45BDD198987915C454EA3FAD14BFFE6E817D8E8C960` |
| CLI executable | `dist/windows/bytefray-cli/bytefray-cli.exe` | 2,871,047 | `2773A627452B8ADFA00EFC841B53BADD6BA254511EE6526C04C9734F70F99944` |
| Agent Designer | `dist/windows/bytefray-agent-designer/bytefray-agent-designer.exe` | 4,266,504 | `FB854FE675949C0AA849F1E588DF25E438CC8D2E902C9B3D9B36FD5775C301DF` |
| Replay Viewer | `dist/windows/bytefray-replay-viewer/bytefray-replay-viewer.exe` | 3,939,077 | `2F312EF61A279D95D7238590979EB009EA6A2F56F3EE593C32B8CDCF507909CE` |
| Windows installer | `Bytefray-Setup-5.0.0-rc1.exe` | 101,250,042 | `F6F2E21306ACF97425BBBC6422BEEA9CAF7ACCA0C55F9044D76580B6FABE13BA` |

The installer's product metadata reports `5.0.0rc1`; the unified and CLI
executables report the same version through `--version`.

The Python build emitted setuptools deprecation warnings for the TOML license
table and license classifier, with a stated future deadline of February 18,
2027. They did not affect this build. No RC1 change was made for a future
tooling migration.

## 9. Artifact content and purity

`tools/check_wheel.py` passed against the new wheel. Direct wheel/sdist
inspection additionally found:

- metadata name `bytefray`, version `5.0.0rc1`, and `Requires-Python >=3.10`;
- all expected `app`, `battle_client`, and `battle_engine` packages;
- all four console entry points and all four authoring-template families;
- all 21 starter manifests;
- all 17 Python-starter sources; `runner`, `seeker`, `spiral`, and `writer`
  are the expected manifest-only VM starters;
- no absolute archive members, backslash-spelled members, or parent traversal;
- no `__pycache__`, `.pyc`, `.pyo`, pytest cache/temp, tests, local logs,
  editor metadata, build/dist directories, local Octave fixture, or V6
  research material;
- no `C:\Users\rasat` or `D:\Projects\BATTLE2` content leak.

The wheel contained 215 members. The sdist contained 221 files (283 tar
members including directories). The four Windows onedir trees contained
respectively 288, 67, 286, and 91 files, with zero cache/purity findings.
Binary/text scans of `dist/windows` and `dist/installer` found no local
developer path. The installer was built only from those four trees plus the
tracked README and LICENSE.

## 10. Clean Windows package-install qualification

### Wheel

A fresh venv at `build/phase2-c9a092b/wheel-env` installed the exact wheel,
with `PYTHONPATH` and `VIRTUAL_ENV` removed and the working directory below a
separate smoke root. `battle_engine.__file__` resolved to that venv's
`site-packages`, and the repository root was absent from `sys.path`.

The following passed:

- `bytefray --version`, `--help`, and `bytefray agents`;
- exact 21-starter discovery and all 17 Python-starter validations;
- stable-v4 pairwise match with result/summary/replay;
- headless playback of the generated replay;
- Dual Team `raider_share=0.7`;
- Dual Team `raider_share=0.33` in a three-entrant match;
- a three-agent/three-match tournament;
- API-v2 annotated scaffold create and validate;
- `agents test` development workflow with result/replay/summary/trace;
- a small stable-v4 evaluation; and
- installed Replay History discovery: 14 scanned and inserted occurrences,
  14 valid, 14 replay-available, zero degraded/incomplete/invalid/inaccessible,
  all under recorded `bytefray-rules-4`.

### Sdist

A second fresh venv built and installed exclusively from the exact sdist.
Imports resolved to that environment's `site-packages`, and a direct check
confirmed the source checkout was not on `sys.path`. Version, 21-agent
catalog, Dual Team validation, stable-v4 `raider_share=0.7` match, and
headless replay passed.

The ephemeral wheels produced from the sdist differed in outer ZIP hash from
the canonical wheel because build time/platform metadata affects the wheel
container. No bit-for-bit sdist-to-wheel reproducibility claim is made; both
sdist-installed runtime checks passed.

## 11. Windows frozen applications and installer

### Frozen application payload: passed

`tools/build_win.ps1` passed all built-in release smokes, including both
Designer startup paths, all four scaffold variants, validation of both API-v2
variants, frozen-payload cache purity, and confirmation that startup did not
write runtime data into the distributable trees.

An additional checkout-independent frozen smoke used the new unified and
Replay Viewer trees with empty `PYTHONPATH`/`VIRTUAL_ENV` and an isolated data
root. It passed:

- `5.0.0rc1` version and help;
- all 21 bundled starters;
- bundled `v5_dual_team` validation;
- `raider_share=0.7` stable-v4 execution;
- headless replay through the standalone frozen viewer; and
- a three-agent stable-v4 tournament.

### Installer construction: passed

Inno Setup compiled `Bytefray-Setup-5.0.0-rc1.exe` successfully from the new
frozen trees. Its hash and size are in section 8.

### Exact-candidate installer lifecycle: PASS

Before the lifecycle, the machine contained the previously qualified RC1
installation at `C:\Program Files\Bytefray` (the earlier `bfd3bb8` candidate)
and machine data root `C:\ProgramData\Bytefray` with 560 pre-existing files.
No installed Bytefray process was running. Immediately before use, the
installer was re-measured at 101,250,042 bytes, SHA-256
`F6F2E21306ACF97425BBBC6422BEEA9CAF7ACCA0C55F9044D76580B6FABE13BA` — unchanged
from section 8, confirming no rebuild or substitution.

An operator was present and accepted the single UAC elevation prompt for an
elevated PowerShell host; every subsequent step ran inside that one elevated
process, so no further prompts were needed. Sequence and results, from the
elevated transcript (`build/phase2-c9a092b/installer-lifecycle-logs/
elevated-lifecycle-transcript.txt`, gitignored):

1. **Predecessor removal.** `C:\Program Files\Bytefray\unins000.exe
   /VERYSILENT /SUPPRESSMSGBOXES /NORESTART` exited 0; the predecessor
   application directory was confirmed absent afterward.
2. **Isolated clean install / upgrade / uninstall lifecycle**
   (`tools/smoke_after_install.ps1 -InstallerPath <exact installer>
   -AppDir "C:\Program Files\Bytefray" -DataRoot <isolated test root>
   -Lifecycle`): initial silent install set machine `BYTEFRAY_ROOT` to the
   isolated root and passed the full installed-application smoke (bundled
   pMARS resources, writable data directories, Start Menu shortcuts, Designer
   sibling-executable layout, `--help` on all three CLI-facing executables,
   Agent Designer GUI startup hold, a starter `seeker`-vs-`writer` match with
   replay, Replay Viewer GUI startup hold on that replay, a bundled pMARS
   match, and safe rejection of an invalid `PMARS_CMD`). A user agent manifest
   was then hand-modified and a user sentinel file added; the exact same
   installer was silently reinstalled as an upgrade over itself, the full
   smoke passed again, and both the modified manifest hash and the sentinel
   file were confirmed unchanged/present. The registered uninstaller then
   exited 0, the application directory and both Start Menu shortcuts were
   confirmed absent, machine `BYTEFRAY_ROOT` was confirmed absent, no
   installed process remained, and the user sentinel file was confirmed
   **retained** in the isolated data root across the uninstall.
3. **Exact-candidate clean reinstall.** With no Bytefray registration
   remaining, `Bytefray-Setup-5.0.0-rc1.exe /VERYSILENT /SUPPRESSMSGBOXES
   /NORESTART` (declared default paths) exited 0. The installed unified
   executable hash matched the qualified `dist/windows` payload exactly
   (`67ACBBCD56FF31AAB236B45BDD198987915C454EA3FAD14BFFE6E817D8E8C960`,
   section 8); machine `BYTEFRAY_ROOT` was exactly `C:\ProgramData\Bytefray`;
   `--version` reported `Bytefray 5.0.0rc1, Agent API v2, result schema v2,
   replay schema v4, Python 3.13.14`. The pre-existing real
   `C:\ProgramData\Bytefray` file count was unchanged at 560 files (no
   existing real user data was lost across the whole lifecycle).
4. **Post-reinstall smoke** (`tools/smoke_after_install.ps1` against the real
   installed paths, no `-Lifecycle`): the same full installed-application
   smoke passed again against the just-reinstalled real candidate, including
   the Agent Designer and Replay Viewer GUI startup holds and the starter
   match/replay.
5. **Starter discovery, on the real final installed candidate.** Running
   `agents` against the long-lived real `C:\ProgramData\Bytefray` first
   reported 23 entries; inspection found this came from two pre-existing
   local fixtures unrelated to this candidate (`Octave`, the known unbundled
   research fixture referenced elsewhere in this document, and `tester1`, an
   old manual-testing leftover) already resident in that non-fresh root, not
   from the installer. Repeating the discovery in a fresh, isolated data root
   (matching the fresh-root methodology used everywhere else in this
   document) reported exactly 21 entries whose names matched the canonical
   21-starter list in section 3 exactly, with no missing and no unexpected
   name.
6. **`agents validate v5_dual_team`** against the real installed candidate:
   `status: valid`, `api_version: 2`.
7. **`v5_dual_team raider_share=0.7` regression**, real installed candidate,
   fresh data root: `run --a-type v5_dual_team --a-param raider_share=0.7
   --b-type v4_quorum --ruleset bytefray-rules-4 --arena 512 --quota 8
   --ticks 30 --seed 602` executed twice; both runs exited 0 and produced
   byte-identical replays, SHA-256
   `DCF24B4EF03BB45446B4A11774713546DD657C0CCD3429E643CD9FAB9A0A3087`.
8. **Final installed state**, independently reconfirmed after the run:
   `C:\Program Files\Bytefray` present with a fresh `unins000.exe`; installed
   unified executable SHA-256 unchanged
   (`67acbbcd56ff31aab236b45bdd198987915c454ea3fad14bffe6e817d8e8c960`); HKLM
   uninstall registration `Bytefray 5.0.0rc1`, version `5.0.0rc1`, install
   location `C:\Program Files\Bytefray\`; both Start Menu shortcuts present;
   machine `BYTEFRAY_ROOT` = `C:\ProgramData\Bytefray`.

No installer or installed-product defect was found. The one anomaly
encountered (the transient 23-count reading) was traced to this session's own
first check using a non-fresh data root, not to the product, the installer,
or an environment gate, and was corrected before being recorded as a result.

A V4-to-V5 installer upgrade was not run; no separate established V4
installer fixture exists for this qualification, consistent with every other
Windows package qualification in this document.

## 12. Starter/bootstrap qualification

Starter behavior passed from source, exact wheel on Windows, exact sdist on
Windows, exact wheel on Linux, exact sdist on Linux, and the frozen Windows
unified executable.

- expected and discovered count: 21;
- manifests parsed/discovered: 21/21;
- Python sources imported and dry-run validated: 17/17;
- API-v1 starters remained API v1; all ten `v4_*`/`v5_*` process starters
  remained Agent API v2 and compatible with stable Ruleset v4;
- fresh data roots were used, so no older copied starter was mistaken for
  packaged content; and
- the Phase 1 repair did not change bootstrap count or identity.

The unbundled Octave copy was used only as an isolated test fixture after the
packaged 21-starter inventory had already been established. It was not added
to any distribution artifact.

## 13. Major workflow smoke

| Workflow | Evidence | Result |
|---|---|---|
| Stable-v4 pairwise match | exact wheel, frozen app, Linux wheel | PASS |
| Three-entrant match | exact wheel on Windows and Linux | PASS |
| Tournament | exact wheel and frozen app on Windows; exact wheel on Linux | PASS |
| Replay generation/headless playback | wheel, sdist, frozen viewer, Linux wheel/sdist | PASS |
| Replay History | installed wheel in-memory rebuild over real smoke artifacts; 14 valid rows | PASS |
| Agent Designer startup | full native GUI suite, both frozen startup smokes in `build_win.ps1`, and the installed-candidate lifecycle GUI holds | PASS |
| Development/Test | installed wheel `agents test` with result/replay/summary/trace | PASS |
| Evaluation | installed wheel stable-v4 evaluation | PASS |
| Agent create/validate | installed wheel API-v2 annotated flow | PASS |
| Parameterized starter | `v5_dual_team` `0.7`/`0.33` across package forms | PASS |

This was a compact release integration smoke, not a new exhaustive UX audit.

## 14. Adversarial non-regression smoke

The fixed-seed sample used the exact clean-wheel installation. Octave was
copied from the local, gitignored fixture into only that isolated data root.
Every match used stable `bytefray-rules-4`; no balancing criterion was imposed.

| Match | Seed / ticks | Result | Replay SHA-256 |
|---|---:|---|---|
| Octave A vs Quorum B | 1 / 40 | A at tick 8 | `ECA3FF32AD99439F62502DF061931027B3F13D424B974563414BF619D3CEF344` |
| Quorum A vs Octave B | 1 / 40 | tie at tick 40 | `456D5BD10258DCCAF6A0F7BBE2D0C0B51B321DA4BF5912C1F002211A244E8167` |
| Quorum vs Core Defender | 101 / 40 | A at tick 17 | `507BDF5D3FA1492135D09D88E17214278CC0AA1C34F6088E56E14076380B6DFE` |
| Dual Team default vs Quorum | 202 / 40 | B at tick 8 | `97E952E5F938725EB34BC3E37B4B5258813CF1C14C4FDA455D7202FDB9B37FFA` |
| Dual Team `0.7` vs Quorum | 202 / 40 | B at tick 33 | `6F24546EC9A05C2A6AEAA339590F386C89B00807CADB2C4438EA85590A800D0D` |
| Dual Team `0.33` / Quorum / Core Defender | 303 / 40 | tie at tick 40 | `B544EA904DA68CC7D2ED1BAA6F19568FE1D41D0E47AE8B8E02F600A98DF86701` |

The default and `0.7` runs reproduced the same match IDs and replay hashes
observed through the source smoke. The sample exposed no accidental packaged
behavioral drift.

## 15. Linux cross-platform qualification

Environment: Ubuntu `24.04.3 LTS` under WSL2, kernel
`6.6.87.2-microsoft-standard-WSL2`, x86_64, CPython `3.12.3`.

Linux first verified the exact transferred artifacts with `sha256sum
--check --strict`; both hashes matched section 8. It then created separate
fresh `/tmp` venv/data/work roots for the wheel and sdist.

Exact invocation:

```text
wsl.exe -d Ubuntu -- bash \
  /mnt/d/Projects/BATTLE2/build/phase2-c9a092b/linux_package_qualification.sh
```

Wheel qualification passed version/help, isolated `site-packages` provenance,
absence of PySide6 and pygame from the headless environment, 21-starter
discovery, all 17 Python-starter validations, stable-v4 pairwise and
three-entrant matches, headless replay, `raider_share=0.7` and `0.33`, a
three-agent tournament, and API-v2 annotated create/validate.

Sdist qualification independently built and installed the exact tarball, then
passed isolated import provenance, version, 21-starter discovery, Dual Team
validation, the `0.7` match, and headless replay. Both explicitly named WSL
qualification roots were resolved beneath `/tmp`, removed after the pass, and
verified absent.

Linux packaged qualification status: **PASS**.

## 16. Release-document consistency

Review found no material active-document contradiction:

- README identifies Python 3.10-3.14, Windows AMD64 and Linux x86_64,
  stable `bytefray-rules-4`, Agent API v2, and active `5.0.0-rc1`;
- CHANGELOG begins with the dated RC1 entry and accurately summarizes its
  current release surface;
- SECURITY names stable `4.0.0` and current prerelease `5.0.0rc1`;
- COMPATIBILITY distinguishes stable v4 from the historical alpha identities
  and records stable-v4 evaluation schema/identity v7;
- the starter guide names exactly the four V5 educational starters and their
  stable-v4/API-v2 boundary; and
- current install commands and platform statements match the built package
  and the exercised headless workflows.

No current documentation calls stable Ruleset v4 an alpha or calls Agent API
v2 experimental. Historical Alpha references were preserved.

## 17. Known reproduced caveats

1. Native Windows GUI pytest prints COM diagnostic `0x8001010d` from the
   Linux-named Designer startup smoke, then passes the complete GUI suite.
2. Setuptools warns that the current license table/classifier representation
   will require migration before February 18, 2027; current artifacts build.

No other current caveat was reproduced. The exact-candidate Windows installer
lifecycle, previously pending after a canceled UAC request, has since
completed and passed (section 11) and is no longer a caveat.

## 18. Deferred future research

No V6 design or balancing work was performed. The retained research topics
are the Phase 0 classifications only: reach economics/bounds and the strategic
effects of last-mover timing and dispersed-process disruption resistance.
Ownership-based localization remains an accepted advanced strategy rather
than a research-required defect.

## 19. Final repository and process state

Final checks confirmed:

- branch `v5-research`; source qualified at `c9a092bfedbdb626551482049ed1f207fe58a191`
  (see the git-state note in section 2 regarding a pre-existing further commit
  on HEAD, which this qualification did not amend, reset, or rely on as
  evidence);
- every source-build artifact size and SHA-256 still matched section 8, and
  the installed Windows candidate's hash matched it exactly at every
  checkpoint in section 11;
- no Windows Python, pytest, PyInstaller, Inno Setup, or Bytefray process
  remained after the lifecycle;
- no WSL Python, pytest, or Bytefray process remained, and both explicitly
  named WSL qualification roots were absent;
- `.git/index.lock` remained absent; and
- this file was modified in the working tree to record section 11's real
  Windows lifecycle results and the gate change in section 1; it was left
  **uncommitted**, as instructed for this qualification run.

Generated artifacts, isolated package environments, and qualification helpers
live only in gitignored `build/`, `dist/`, and pytest-temp paths. No commit,
tag, version bump, artifact rebuild, upload, publication, or release creation
was performed. The exact RC1 candidate remains installed at
`C:\Program Files\Bytefray` after the completed lifecycle qualification.
