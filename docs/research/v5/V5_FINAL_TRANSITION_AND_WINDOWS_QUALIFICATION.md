# Bytefray 5.0.0 Final Transition and Windows Qualification — Phase 3

Phase 3 transitions the qualified RC1 candidate to final release identity
`5.0.0` and independently re-qualifies the exact final Windows artifacts. It
does not change gameplay, the Agent API, Ruleset v4, or the V5 starter
roster.

## 1. Baseline

| Item | Value |
|---|---|
| Branch | `v5-research` |
| Starting HEAD | `0cc665d14cf7316bf5d26d5d884e698a4218558e` |
| Upstream | `origin/v5-research`; ahead 1 / behind 0 |
| Initial `git status --short` | empty |
| `.git/index.lock` | absent |
| Existing stashes | two pre-existing entries (`On main: sync_win auto-stash 20251001-214422`; `On feature/pygame-window-fit: WIP before pulling main`); inventoried and untouched |
| Running pytest/Python/Bytefray/build processes | none found |
| Qualified source candidate | `c9a092bfedbdb626551482049ed1f207fe58a191` |

## 2. Post-RC1 commit audit

Two commits exist between the qualified source candidate and the Phase 3
starting HEAD:

| Commit | Subject | Files changed | Classification |
|---|---|---|---|
| `ae7505b626e7132a04d3c215061b5153cc96659c` | `RC1 QUALIFICATION PASSED — READY FOR FINAL 5.0.0 TRANSITION` | `docs/research/v5/V5_RC1_FINAL_QUALIFICATION.md` (new file, 480 insertions) | Qualification documentation only |
| `0cc665d14cf7316bf5d26d5d884e698a4218558e` | `docs(v5): finalize RC1 qualification` | `docs/research/v5/V5_RC1_FINAL_QUALIFICATION.md` (130 insertions, 48 deletions) | Qualification documentation only |

`git diff --stat c9a092b..0cc665d` touches only
`docs/research/v5/V5_RC1_FINAL_QUALIFICATION.md`, which does not exist at
`c9a092b` (`git cat-file -e c9a092b:docs/research/v5/V5_RC1_FINAL_QUALIFICATION.md`
fails). **Invariant confirmed: no production, gameplay, scheduler, Agent
API, or Ruleset change exists after the qualified source candidate.** All
post-RC1 work is qualification documentation.

The RC1 report's own git-state note documents a pre-existing, already
investigated discrepancy (commit `ae7505b`'s message vs. its file content at
the time). That discrepancy is historical and was not touched in Phase 3, per
task instruction.

### RC1 qualification record confirmed

`docs/research/v5/V5_RC1_FINAL_QUALIFICATION.md` records gate
`RC1 QUALIFICATION PASSED — READY FOR FINAL 5.0.0 TRANSITION` (section 1) and
a completed exact-candidate Windows installer lifecycle (section 11):
installer hash `F6F2E21306ACF97425BBBC6422BEEA9CAF7ACCA0C55F9044D76580B6FABE13BA`
(101,250,042 bytes), predecessor removal, isolated install/upgrade/uninstall
with user-data preservation, exact-candidate reinstall, post-reinstall smoke,
21/21 starter discovery in a fresh root, and a deterministic
`v5_dual_team raider_share=0.7` regression. The report was read and confirmed,
not rewritten — it remains an RC1 historical record.

## 3. Version-surface inventory

Searched active production/release-facing files for
`5.0.0-rc1` / `5.0.0rc1` / `5.0.0-alpha` / `5.0.0a1` / `RC1` / `Release
Candidate` (85 files matched at least one pattern). Classification:

### ACTIVE RELEASE SURFACE (transitioned to final 5.0.0)

| File | Surface |
|---|---|
| `pyproject.toml` | `version = "5.0.0-rc1"` → `"5.0.0"` |
| `tools/installer.iss` | `AppVersion "5.0.0rc1"` → `"5.0.0"`; `ReleaseTag "5.0.0-rc1"` → `"5.0.0"` |
| `README.md` | "active release candidate is Bytefray 5.0.0-rc1" → current stable release 5.0.0; heading `Development Line` → `Current Release` |
| `SECURITY.md` | most-recent-stable/current-prerelease language → single current stable release `5.0.0` |
| `docs/ROADMAP.md` | "current development generation... release candidate" → "current stable generation... current release" |
| `docs/COMPATIBILITY.md` | "V5 release candidate" → "current V5 release" |
| `CHANGELOG.md` | new `## [5.0.0] - 2026-09-15` final entry added above the preserved `## [5.0.0-rc1]` entry |
| `engine/tests/test_v5_alpha1_phase_b_engine_hygiene.py` | `test_version_transition_5_0_0rc1` (asserted `5.0.0-rc1`/`5.0.0rc1`) renamed to `test_version_transition_5_0_0` and updated to assert final `5.0.0` across `pyproject.toml`, `installer.iss`, and installed package metadata |

### HISTORICAL RC1 EVIDENCE (left unchanged)

`docs/research/v5/V5_RC1_FINAL_QUALIFICATION.md`,
`V5_RC1_PROCESS_SHARE_REMEDIATION.md`, `V5_RC1_ADVERSARIAL_FINDINGS_INTAKE.md`,
`V5_RC1_WINDOWS_PACKAGE_QUALIFICATION.md`,
`V5_RC1_BLOCKER_REMEDIATION_AND_SOURCE_REQUALIFICATION.md`,
`V5_RC1_READINESS_AND_QUALIFICATION.md`, and the existing
`## [5.0.0-rc1]` / `## [5.0.0a1]` CHANGELOG entries.

### HISTORICAL/ARCHIVED MATERIAL (left unchanged)

All `docs/research/v4/`, `docs/archive/`, and V5 Alpha-1-phase research
documents under `docs/research/v5/` (`V5_ALPHA1_*`, `V5_REPLAY_HISTORY_*`,
`V5_POST_RELEASE_H1_PARAMETER_CONSISTENCY.md`), plus historical `RC1`/`RC2`
references in `docs/ROADMAP.md`'s v2/v3/v4 milestone sections and
`CHANGELOG.md`'s v1–v4 entries.

### TEST EXPECTATION — investigated, no change needed

`engine/tests/test_check_wheel.py` uses `"5.0.0rc1"` only as synthetic
fixture data for the version-agnostic `tools/check_wheel.py` validator (which
derives the expected version from the wheel filename, not a hardcoded
constant); it does not assert the project's own current version.
`engine/tests/test_result_model.py`, `test_replay_history.py`, and
`test_v5_replay_history_presentation.py` embed `"5.0.0a1"` as an arbitrary
historical `product_version` fixture value inside constructed
result/replay-history payloads, not as an assertion about the current build.
`tests/test_agent_development_panel.py`'s `"""RC1: ..."""` docstring is an
unrelated internal test label, not a release-candidate reference.

### SUSPICIOUS/AMBIGUOUS — investigated, resolved as historical

Numerous `engine/src/battle_engine/*.py` and `engine/tests/*.py` comments
reference "the RC1 default-Ruleset-defect fix" — this is a **V3/V4-era**
historical defect/fix (see `docs/archive/v3/V3_RC1_DEFAULT_RULESET_DEFECT.md`),
unrelated to the V5 RC1 release train. Left unchanged.
`.github/workflows/*.yml` comments narrating past RC1 events ("during RC1
manual testing") are historical narrative, not version pins. Left unchanged.
`tools/check_wheel.py` and `app/services/ruleset_options.py` comments citing
`docs/research/v4/V4_RC1_PHASE2_STABLE_CONTRACT_PROMOTION.md` are doc
cross-references, not version identity. Left unchanged.

No occurrence of `5.0.0-alpha`/`5.0.0a1` was found describing the *current*
release identity outside historical "added in v5.0.0a1" feature-introduction
notes, which were preserved per the same policy the RC1 report itself
recorded.

## 4. Functionality freeze

No gameplay, scheduler, scoring, quota-allocation, process-reach,
disruption, core-capture, replay-semantics, Agent API, Ruleset-v4, or
starter-agent logic was changed. No starter agent was added, removed, or
rebalanced; the V5 starter roster remains exactly the 21 identifiers
qualified in RC1. No V6 work, starter-prefix rename, starter regrouping, or
Octave bundling was performed. All edits in section 3 are
version/documentation/build-metadata only.

## 5. Pre-build source verification

Environment: Windows 11 build `10.0.26120`, AMD64, CPython `3.13.14`.

A stale, gitignored `bytefray.egg-info/` directory at the repo root (dated
before this session, not tracked in git, produced by an earlier legacy-style
editable install) was found to shadow the real package version whenever the
working directory landed on `sys.path` first (`python -c`/`python -m`
invocations resolved `5.0.0rc1` from it while the installed console-script
entry points correctly resolved `5.0.0` from `site-packages`). It was removed
as disposable, regenerable build cruft; `pip install -e . --no-deps
--no-build-isolation` was then used to refresh the editable install's
`site-packages` metadata (`bytefray-5.0.0.dist-info`) from the edited
`pyproject.toml`. After both steps, `importlib.metadata.version("bytefray")`
and `bytefray --version` consistently report `5.0.0`.

| Gate | Result |
|---|---|
| Package version | **`5.0.0`** (`importlib.metadata.version("bytefray")`) |
| CLI `--version` | **`Bytefray 5.0.0, Agent API v2, result schema v2, replay schema v4, Python 3.13.14`** |
| Active release surfaces claiming RC1 | **none** (re-grepped after edits) |
| Historical RC1 records | intact, unchanged |
| Starter count/names | unchanged (no starter edits made) |
| `git diff --check` | **PASS** |
| Ruff (`ruff check .`) | **PASS** |
| Engine mypy (`engine/src/battle_engine`) | **PASS** — 114 source files |
| Client mypy (`client/src/battle_client`) | **PASS** — 16 source files |
| Focused version test (`engine/tests/test_v5_alpha1_phase_b_engine_hygiene.py`) | **PASS** — 9 passed, including renamed `test_version_transition_5_0_0` |

## 6. Permanent Ruleset-v4 equivalence

Command: `pytest engine/tests/test_v4_stable_ruleset_equivalence.py
engine/tests/test_v4_trace_equivalence.py`

Result: **PASS — 25 passed** in 7.73 s. `git status --short` immediately
after showed no vector/golden/reference-file modification.

## 7. Canonical Windows source qualification

| Gate | Exact command | Result |
|---|---|---|
| Canonical source suite | `.\.venv\Scripts\python.exe -m pytest --basetemp=.pytest-tmp/phase3-source` | **PASS** — 3,682 passed, 22 skipped, 0 failed, 0 errors, 3 GUI-marked deselected (`pytest.ini`'s `-m "not gui"` default) in 389.33 s |
| Native Windows GUI suite | `$env:QT_QPA_PLATFORM='windows'; .\.venv\Scripts\python.exe -m pytest tests/ -m gui --basetemp=.pytest-tmp/phase3-gui-retry` | **PASS** — 507 passed, 0 failed, 0 errors in 177.38 s |

Both results match the RC1 source qualification's counts exactly (3,682
passed/22 skipped source; 507 passed GUI), confirming the version/
documentation-only transition did not alter behavior.

The GUI suite reproduced the same known non-failing Windows COM diagnostic
`0x8001010d` from `tests/test_linux_designer_smoke.py` recorded as an RC1
caveat, then continued and passed.

**Caveat — transient GUI-suite hang, not reproducing.** The first GUI-suite
attempt stalled indefinitely after the COM diagnostic, with a `Replay
History` test window left open and its owning process idle (flat CPU,
`Responding: False`) for several minutes. No source file under test had
changed relative to RC1's own clean GUI pass (this session made no gameplay,
GUI, or threading code changes — only version/documentation edits and one
unrelated version-assertion test). The stalled process was terminated and
the suite was re-run from a clean process state; it passed cleanly on retry
with the exact RC1 counts. This is recorded as a one-off local thread-timing
flake in the multithreaded Replay History browser test suite
(`tests/test_v5_replay_history_browser.py`), not a new product defect: the
underlying source is byte-for-byte unchanged since RC1's successful run of
the same suite.

## 8. Commit boundary

Final source SHA: `4be33840b2845518f83a8dc3e6c659605ae2150d`
(`release: prepare Bytefray 5.0.0`), containing exactly the 8 files in
section 3's ACTIVE RELEASE SURFACE table (57 insertions, 17 deletions). This
Phase 3 report remains uncommitted, per the same precedent the RC1 report
itself recorded. `git status -sb` post-commit: `ahead 2` of
`origin/v5-research`, tree clean except this report.

## 9. Final artifact inventory

All artifacts below are built from source SHA `4be33840b2845518f83a8dc3e6c659605ae2150d`.

Build commands (identical to the RC1 procedure, final-SHA output directories):

```text
.\.venv\Scripts\python.exe -m build --no-isolation --outdir dist/phase3-final-4be3384/python
& 'C:\Program Files\PowerShell\7\pwsh.exe' -NoProfile -File tools\build_win.ps1
& 'C:\Users\rasat\AppData\Local\Programs\Inno Setup 6\ISCC.exe' tools\installer.iss
```

| Type | Filename | Bytes | SHA-256 |
|---|---|---:|---|
| Wheel | `bytefray-5.0.0-py3-none-any.whl` | 1,067,857 | `50D632C7EC2C4A939601DFF54C15BF67565C785E084672073CB8C17C1E9F47A5` |
| Sdist | `bytefray-5.0.0.tar.gz` | 975,861 | `8BEE3285179468F06A33DA81067AE66A4F8B1E59FD3C79362D69C369B7D22FBB` |
| Unified executable | `dist/windows/bytefray/bytefray.exe` | 4,272,863 | `D68A4300CE48FC0DAFCFD527B78F09074C3B21E3DFDF473CE2FCBB358983F13A` |
| CLI executable | `dist/windows/bytefray-cli/bytefray-cli.exe` | 2,871,047 | `44341FF5E565A93F669285319356A8835433863B96F019B60D143144CAFCE1D3` |
| Agent Designer | `dist/windows/bytefray-agent-designer/bytefray-agent-designer.exe` | 4,266,504 | `C4D5A40D9F92EBC24D0A8DCAC1511A99008CA434A962A1103ED2A36628FFCBE3` |
| Replay Viewer | `dist/windows/bytefray-replay-viewer/bytefray-replay-viewer.exe` | 3,939,077 | `DF5FFD7D23BB7E55ECC941DAC18B87BD01D9F8ABD5E40550E80DC3007D9F531F` |
| Windows installer | `Bytefray-Setup-5.0.0.exe` | 101,236,541 | `99886EE7FD0A3FE140DD23AE113E009FD374DDA9349C0C316FDB5B029D782205` |

Every frozen executable's byte size is identical to its RC1 counterpart
(hashes differ only because the embedded version string changed from
`5.0.0rc1`/`5.0.0-rc1` to `5.0.0`), and both `build_win.ps1`'s own release
smokes (bytecode/cache purity, branding resource, GUI import/startup, four
`agents create` scaffold variants including both API-v2 forms) and Inno
Setup's compile passed cleanly. A stale, gitignored `bytefray.egg-info/`
reappeared at the repo root as a normal side effect of `python -m build`'s
sdist step (setuptools' in-place `egg_info` command) and was removed again
before proceeding to installation qualification.

### Wheel/sdist purity

`tools/check_wheel.py` passed against the final wheel. Direct inspection
found 215 wheel members (matching RC1's count exactly) and 283 sdist tar
members (matching RC1's count exactly), with no `__pycache__`/`.pyc`/`.pyo`,
no absolute or backslash-spelled archive members, no parent-traversal
members, and no local developer path (`rasat`/`BATTLE2`) leaked into either
archive.

## 10. Final frozen Windows application qualification

All checks run against the exact executables in section 9, using an isolated
`BYTEFRAY_ROOT` (not the machine's real data root).

| Check | Result |
|---|---|
| `bytefray.exe --version` | **PASS** — `Bytefray 5.0.0, Agent API v2, result schema v2, replay schema v4, Python 3.13.14` |
| `bytefray.exe --help` | **PASS** |
| `bytefray-cli.exe` equivalent version/help | **PASS** via `--help` — see caveat below |
| Agent Designer startup (frozen) | **PASS** — held open 6 s, closed cleanly |
| Replay Viewer startup (frozen) | **PASS** — held open 6 s against a real replay, closed cleanly |
| Stable Ruleset-v4 pairwise match (`v4_quorum` vs `v4_claimer`) | **PASS** — result/replay/summary produced |
| Starter discovery (`bytefray agents`) | **PASS** — exactly 21 entries in a fresh root |
| `v5_dual_team raider_share=0.7` regression, run twice | **PASS** — byte-identical replay SHA-256 `DCF24B4EF03BB45446B4A11774713546DD657C0CCD3429E643CD9FAB9A0A3087`, an **exact match to the RC1 report's recorded hash** for the same case (section 11, step 7) |
| Bundled pMARS match (`--mode redcode94`) | **PASS** — exit 0, bundled `pmars.exe`/`COPYING` present under `_internal/pmars/windows/` |
| Invalid `PMARS_CMD` rejection | **PASS** — exit 2, diagnostic `Configured PMARS_CMD executable was not found: ... Correct or unset PMARS_CMD; explicit configuration does not fall back.`, no false-success `summary.json` |

**Caveat — `bytefray-cli.exe` has no `--version` flag; pre-existing, not a
Phase 3 regression.** `engine/src/battle_engine/cli.py` (the `bytefray-cli`
entry point) has never implemented a `--version` flag — only
`battle_engine/command.py` (the unified `bytefray` entry point) does; this
was confirmed identical at the qualified RC1 source SHA `c9a092b` via `git
show`. The RC1 report's section 8 sentence "the unified and CLI executables
report the same version through `--version`" does not hold literally for
`bytefray-cli.exe` — this task's own Section O wording ("`bytefray-cli.exe`
equivalent version/help") anticipates exactly this, so `--help` was used as
the equivalent identity check instead. This is a pre-existing product
characteristic unrelated to the version transition, not a new defect, and is
recorded here as a documentation-accuracy note rather than a release
blocker.

**Caveat — one non-reproducing frozen-app test-harness mistake.** An initial
attempt to hold-test the frozen Replay Viewer used `-Wait` together with the
Agent-Designer-only `BYTEFRAY_GUI_SMOKE_EXIT_MS` auto-exit environment
variable, which the Replay Viewer does not honor (confirmed via
`grep`: only `app/agent_designer.py` reads it); the viewer correctly waited
for its window to be closed, which was mistaken for a hang and the process
was terminated. The corrected check used the project's own
`Test-GuiStartup`-style pattern (launch detached, hold, close) from
`tools/smoke_after_install.ps1`, which passed cleanly. This was a test-script
error, not a product issue.

## 11. Clean Windows package-install qualification

### Wheel

A fresh venv at `build/phase3-final-4be3384/wheel-env` installed the exact
final wheel with `PYTHONPATH`/`VIRTUAL_ENV` removed. `battle_engine.__file__`
resolved to that venv's `site-packages`
(`build/phase3-final-4be3384/wheel-env/Lib/site-packages/battle_engine/__init__.py`),
confirming the repository checkout was not the import source. The following
passed, all against an isolated `BYTEFRAY_ROOT`:

* `bytefray --version` → `Bytefray 5.0.0, ...`; 21/21 starter discovery;
* stable-v4 pairwise match (`v4_quorum` vs `v4_claimer`) with result/replay;
* headless replay playback of the generated replay;
* `v5_dual_team raider_share=0.7` three-entrant match;
* a three-agent tournament (`v4_quorum`, `v4_claimer`, `v5_core_defender`) —
  completed 3/3, 0 failed, standings reported;
* `agents create --api-version 2 --template annotated` + `agents validate`;
* `agents test` development workflow (result/replay/summary/trace); and
* the deterministic `v5_dual_team raider_share=0.7` regression
  (`--arena 512 --quota 8 --ticks 30 --seed 602`), run twice: byte-identical
  replay SHA-256 `DCF24B4EF03BB45446B4A11774713546DD657C0CCD3429E643CD9FAB9A0A3087`
  — an **exact match** to both the RC1 report's recorded hash for this case
  and this session's frozen-app result in section 10.

Two CLI invocation mistakes during this pass (`tournament --agents ...`
instead of positional `agents`; `agents test --b-type` instead of
`--opponent`) were corrected from the executables' own `--help`/usage text;
neither was a product defect.

### Sdist

A second fresh venv built and installed exclusively from the exact sdist.
Imports resolved to that environment's `site-packages`, version reported
`5.0.0`, starter discovery found 21/21, and the same deterministic
`v5_dual_team raider_share=0.7` regression reproduced the identical
`DCF24B...` replay hash.

Across source, the frozen unified executable, the exact wheel, and the exact
sdist, the same deterministic case now produces the identical replay hash
that RC1 itself recorded for it — strong evidence of zero behavioral drift
from the version/documentation-only final transition.

## 12. Exact final Windows installer lifecycle

This phase requires real Windows UAC elevation to install/uninstall against
the machine's actual `C:\Program Files\Bytefray` / `C:\ProgramData\Bytefray`.
This session cannot accept a UAC prompt itself, so a single self-contained
script (`build/phase3-final-4be3384/run_elevated_lifecycle.ps1`, gitignored)
was prepared and the user ran it from one elevated PowerShell host (one UAC
prompt), exactly matching the RC1 report's own "single elevated host, no
further prompts" methodology. Two bugs surfaced and were fixed in that
orchestration script (not in any tracked repository file) before a clean run:

1. **`-notmatch` against a captured multi-line array.** `--version`'s wrapped
   two-line console output was captured as a `string[]`; `-notmatch` against
   an array returns a (non-empty, therefore truthy) filtered array rather
   than a boolean, producing a false "version mismatch" even though the
   version was correct. Fixed by joining the captured lines before matching.
2. **`ProcessStartInfo.ArgumentList` under legacy Windows PowerShell 5.1.**
   `tools/smoke_after_install.ps1`'s `Invoke-ProcessChecked` uses
   `$StartInfo.ArgumentList.Add(...)`, which is unreliable under Windows
   PowerShell 5.1 (Desktop/.NET Framework) but works correctly under
   PowerShell 7. The RC1 report's own build commands already invoke
   `pwsh.exe` for PowerShell-7-dependent tooling (`build_win.ps1`); this
   orchestration script was updated to invoke
   `tools/smoke_after_install.ps1` the same way. This is an invocation-shell
   mismatch in ad hoc orchestration, not a defect in any tracked file, and no
   repository file was changed to work around it.

**Note on step 1's starting state.** An early attempt crashed (on bug 1,
above) before reaching the actual upgrade install call, so its own
pre-check still read the real machine as the qualified RC1 build
(`67ACBBCD...`, version `5.0.0rc1`) — consistent with this session's very
first pre-Phase-P check. By the time the first fully-passing run started, the
real machine was already reading as the final build; the exact transcript of
that specific RC1-origin transition was not captured in one clean run.
Independently, across that whole window this session repeatedly confirmed:
the real `ProgramData` file count stayed at 966 throughout (no data loss),
and the final state — registry `DisplayVersion 5.0.0`, correct
`InstallLocation`, correct `BYTEFRAY_ROOT`, correct Start Menu shortcuts, and
an installed `bytefray.exe` hash exactly matching this session's qualified
frozen build — is fully verified. The clean run below additionally exercised
a full real-path upgrade-reinstall (over the by-then-already-final build),
which validates the upgrade-in-place mechanics themselves even though it was
not, in that specific run, an RC1-origin transition.

### Clean elevated run — full transcript result: PASS

Installer re-verified immediately before use: 101,236,541 bytes, SHA-256
`99886EE7FD0A3FE140DD23AE113E009FD374DDA9349C0C316FDB5B029D782205` —
unchanged from section 9.

| Step | Result |
|---|---|
| 1. Real-path upgrade install (`/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`) | **PASS** — exit 0 |
| 2. Version/registration verification | **PASS** — `Bytefray 5.0.0, ...`; registry `DisplayName=Bytefray 5.0.0`, `DisplayVersion=5.0.0`; installed exe hash `D68A4300...` matches section 9 exactly |
| 3. Post-upgrade smoke (`tools/smoke_after_install.ps1`, real paths) | **PASS** — `bytefray`/`bytefray-cli`/`bytefray-replay-viewer` `--help`; Agent Designer GUI startup hold; starter `seeker` vs `writer` match + replay; Replay Viewer GUI startup hold; bundled pMARS match; invalid `PMARS_CMD` rejected with the normalized diagnostic; no leftover installed process — `=== SUCCESS ===` |
| 4. Real user-data preservation across upgrade | **PASS** — 966 files before and after (smoke adds files but nothing was lost) |
| 5. Uninstall (`unins000.exe /VERYSILENT ...`) | **PASS** — `C:\Program Files\Bytefray` removed; `C:\ProgramData\Bytefray` and its 966 files retained; machine `BYTEFRAY_ROOT` removed; both Start Menu shortcuts removed |
| 6. Clean final 5.0.0 install (real default paths) | **PASS** — machine `BYTEFRAY_ROOT` restored to `C:\ProgramData\Bytefray`; installed exe hash matches; 966 real files still present |
| 7. Post-clean-install smoke | **PASS** — identical full smoke to step 3, `=== SUCCESS ===` |
| 8. Starter discovery, fresh isolated root | **PASS** — exactly 21/21, matching the canonical list |
| 9. `agents validate v5_dual_team`, real installed candidate | **PASS** — `status: valid`, `api_version: 2` |
| 10. `v5_dual_team raider_share=0.7` regression, run twice | **PASS** — byte-identical replay SHA-256 `DCF24B4EF03BB45446B4A11774713546DD657C0CCD3429E643CD9FAB9A0A3087`, an **exact match** to the RC1 report's recorded hash, and to this session's frozen-app, wheel, and sdist checks in sections 10-11 |
| 11. Final installed state re-confirmation | **PASS** — `AppDir` present, `unins000.exe` present, exe hash matches, registry `DisplayVersion=5.0.0`/correct `InstallLocation`, both Start Menu shortcuts present, machine `BYTEFRAY_ROOT` correct, real `ProgramData` file count unchanged at 966 |

No installer or installed-product defect was found. `WINDOWS FINAL 5.0.0
QUALIFICATION` installer-lifecycle gate: **PASS**.

## 13. Major Windows workflow smoke

Across source, the exact wheel, the exact sdist, the frozen unified
executable, and the real installed final candidate over the course of this
phase:

| Workflow | Evidence | Result |
|---|---|---|
| Stable-v4 pairwise match | source, wheel, sdist, frozen exe, installed candidate | PASS |
| Three/multi-entrant match | wheel (`v5_dual_team` 3-entrant), installed candidate (adversarial multi-agent) | PASS |
| Tournament | wheel (`v4_quorum`/`v4_claimer`/`v5_core_defender`, 3/3 completed, standings reported) | PASS |
| Replay generation / headless playback | wheel | PASS |
| Agent Designer startup | frozen build's own smoke, installed-candidate lifecycle smoke (x2) | PASS |
| Replay Viewer startup | frozen app (held with a real replay), installed-candidate lifecycle smoke (x2) | PASS |
| Development/Test (`agents test`) | wheel — result/replay/summary/trace produced | PASS |
| Evaluation (`agents evaluate`) | real installed candidate — `v4_quorum` vs `v4_claimer`, 4 matches, full behavior/win-rate report | PASS |
| Agent create/validate | frozen exe and wheel — API-v2 annotated scaffold | PASS |
| Parameterized starter (`v5_dual_team`) | source, frozen exe, wheel, sdist, installed candidate — deterministic across all five | PASS |

## 14. Adversarial non-regression smoke

Ran the compact fixed-seed sample named in the task (Octave vs Quorum both
seats; Quorum vs one standard agent; one multi-agent match), using the local
gitignored `agents/Octave` fixture copied into an isolated data root, first
against the real installed final candidate and then, identically, against
this session's source checkout:

| Match | Seed/ticks | Installed-candidate hash | Source hash | Match? |
|---|---:|---|---|---|
| Octave A vs Quorum B | 1/40 | `0F8723F1...294D` | `0F8723F1...294D` | **identical** |
| Quorum A vs Octave B | 1/40 | `3FB5225E...87236` | `3FB5225E...87236` | **identical** |
| Quorum vs Core Defender | 101/40 | `B797438D...0503E` | `B797438D...0503E` | **identical** |
| Dual Team 0.33 / Quorum / Core Defender | 303/40 | `9A8A1947...93D23` | `9A8A1947...93D23` | **identical** |

All four are byte-identical between source and the packaged/installed final
candidate, confirming no packaging-related behavioral drift — the actual
purpose of this check. None of the four matches the RC1 report's own
section-14 hash for the same seed/ticks pair; this is expected and not a
regression indicator: RC1's section 14 did not state the arena/quota values
it used for that table (unlike the fully-specified `v5_dual_team` case in
section 7, which *is* meant to be an exact cross-release fixture and which
this session reproduced exactly — see sections 10-12), so RC1's own
adversarial table was itself a same-session source-vs-packaged consistency
check, not a byte-for-byte regression baseline. This session's own
source-vs-packaged comparison serves that identical purpose and passes.
Octave's relative strength is not treated as a release defect, and Octave was
not packaged into any artifact.

## 15. Final documentation audit

Re-grepped every canonical active release surface (`README.md`,
`SECURITY.md`, `docs/ROADMAP.md`, `docs/COMPATIBILITY.md`,
`docs/V5_STARTER_AGENTS.md`, `pyproject.toml`, `tools/installer.iss`) for
`5.0.0-rc1`/`5.0.0rc1`: no matches. `Bytefray-Setup-5.0.0` (the real,
built artifact name) appears only in this report and in historical RC1/Alpha
research documents, as expected — no active document hardcodes a versioned
filename; README's install instructions use `pip install bytefray` and
`Bytefray-Setup-*.exe` (both already version-agnostic and unchanged) and
correctly describe the real download/install path. Historical RC1
qualification records remain untouched.

## 16. Linux qualification deferral (Section U)

Linux final qualification is explicitly deferred to the next phase, per task
instruction. The exact final wheel and sdist below are preserved unchanged
under `dist/phase3-final-4be3384/python/` for that phase and must not be
rebuilt:

| Artifact | Filename | Bytes | SHA-256 |
|---|---|---:|---|
| Wheel | `bytefray-5.0.0-py3-none-any.whl` | 1,067,857 | `50D632C7EC2C4A939601DFF54C15BF67565C785E084672073CB8C17C1E9F47A5` |
| Sdist | `bytefray-5.0.0.tar.gz` | 975,861 | `8BEE3285179468F06A33DA81067AE66A4F8B1E59FD3C79362D69C369B7D22FBB` |

Final source SHA for both: `4be33840b2845518f83a8dc3e6c659605ae2150d`.

## 17. Publication status

No tag was created, no GitHub release was created, nothing was uploaded to
PyPI, and the installer was not published anywhere beyond this local
qualification. Publication remains explicitly withheld pending Linux
qualification and explicit approval, per task instruction.

## 18. Final repository and process state

- Branch `v5-research`, final source SHA `4be33840b2845518f83a8dc3e6c659605ae2150d`.
- `git status --short`: only this report is untracked
  (`docs/research/v5/V5_FINAL_TRANSITION_AND_WINDOWS_QUALIFICATION.md`); the
  final-transition commit itself is clean/tracked.
- `ahead 2` of `origin/v5-research` (the pre-existing RC1-doc commit plus
  this session's final-transition commit); nothing was pushed.
- The two pre-existing stashes noted in section 1 remain untouched.
- No Python, pytest, PyInstaller, or Inno Setup process remains running.
- Generated artifacts, isolated package/venv environments, and this
  session's helper scripts live only under gitignored `build/`, `dist/`, and
  `.pytest-tmp/` paths; nothing outside those paths was modified besides the
  tracked final-transition commit and this report.
- This report is deliberately left **uncommitted**, matching the RC1
  report's own precedent, for review before any further action.

## 19. Final release gate

    WINDOWS FINAL 5.0.0 QUALIFICATION PASSED —
    EXACT FINAL WHEEL/SDIST READY FOR LINUX QUALIFICATION

This is not the publication gate. No tag, release, or publication has been
created or approved.
