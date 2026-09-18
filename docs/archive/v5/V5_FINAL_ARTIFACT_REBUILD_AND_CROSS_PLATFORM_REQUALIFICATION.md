# Bytefray 5.0.0 Final Artifact Rebuild and Cross-Platform Requalification — Phase 4B

Phase 4B rebuilds the complete Bytefray 5.0.0 final artifact set from the
Phase 4A replay-newline remediation lineage and proves the exact artifacts are
release-ready on Windows and Linux. This phase makes no gameplay, scheduler,
scoring, Agent API, Ruleset, or starter-agent change; it is a rebuild and
requalification of artifacts only.

## 1. Canonical source SHA and remediation ancestry

| Item | Value |
|---|---|
| Branch | `v5-research` |
| `FINAL_SOURCE_SHA` | `6827ae58d969ddbe483f3601749bb78014aa2c5f` |
| Upstream | `origin/v5-research`; 0 ahead / 0 behind at start |
| `git status --short` at start | empty |
| `.git/index.lock` | absent |
| Running pytest/Python/Bytefray/build processes at start | none found |
| Existing stashes | two pre-existing, unrelated (`On main: sync_win auto-stash 20251001-214422`; `On feature/pygame-window-fit: WIP before pulling main`) — inventoried, untouched |

Ancestry confirmed with `git merge-base --is-ancestor`, not inferred from
branch naming or commit prose:

- `4be3384` ("release: prepare Bytefray 5.0.0") is an ancestor of
  `FINAL_SOURCE_SHA`: **confirmed**.
- `314ccda` ("fix(v5): canonicalize replay newlines across platforms") is an
  ancestor of `FINAL_SOURCE_SHA`: **confirmed**.
- `v5-final-replay-newline-fix` was already fast-forward-merged into
  `v5-research` before this phase began (`git merge-base --is-ancestor
  v5-final-replay-newline-fix v5-research` → true); Section B's reconciliation
  step required no action.

Log from `4be3384` to `FINAL_SOURCE_SHA`:

```
6827ae5 docs(v5): record Windows verification of replay newline remediation
314ccda fix(v5): canonicalize replay newlines across platforms
61d5abb docs(v5): record final Windows qualification
4be3384 release: prepare Bytefray 5.0.0
```

`git status --short` remained clean at every checkpoint of this phase, and
`HEAD` remained `6827ae58d969ddbe483f3601749bb78014aa2c5f` throughout — no
source or documentation change was made prior to this report, per the task's
"freeze the source SHA" requirement.

## 2. Pre-build source sanity (Section D)

Run against `FINAL_SOURCE_SHA` in the repository's `.venv` (editable install,
source-resolving), a fresh isolated `BYTEFRAY_ROOT` (not the persistent
`%ProgramData%\Bytefray` catalog):

| Gate | Result |
|---|---|
| Newline regression (`test_replay_newline_canonicalization.py`) | **PASS** — 5 passed |
| Ruleset-v4 equivalence (`test_v4_stable_ruleset_equivalence.py` + `test_v4_trace_equivalence.py`) | **PASS** — 25 passed |
| Exact source fixed-seed regression | **PASS** — 23,171 bytes, 0 CRLF, SHA-256 `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` — exact match |

`git status --short` remained clean after this set.

## 3. Build commands

```
python -m build --wheel --sdist --outdir dist/phase4b-final-6827ae5
powershell -File tools\build_win.ps1
"C:\Users\rasat\AppData\Local\Programs\Inno Setup 6\ISCC.exe" tools\installer.iss
```

`tools/build_win.ps1` builds all four PyInstaller onedir applications and runs
its own built-in qualification gates unconditionally as part of the build
(bytecode/cache contamination check, branding-resource presence check, GUI
import/startup smoke for the unified dispatcher's `design` subcommand and the
standalone Designer, and `agents create`/`agents validate` smoke across all
four (API version, template) combinations against the actual frozen
`bytefray.exe`, each isolated to its own throwaway `BYTEFRAY_ROOT`) — all of
which passed with exit code 0. `tools/installer.iss` reads its payload from
`dist/windows` (the `build_win.ps1` output) and writes to `dist/installer`, so
the installer was compiled directly from the same build output verified
above.

Outputs were copied (not moved, to preserve Phase 3's `dist/phase3-final-4be3384/`
and the original `dist/windows`/`dist/installer` build locations untouched)
into the new, phase-distinct path `dist/phase4b-final-6827ae5/`.

## 4. Complete artifact inventory

All source SHA: `6827ae58d969ddbe483f3601749bb78014aa2c5f`.

| Artifact | Path | Bytes | SHA-256 |
|---|---|---|---|
| Wheel | `dist/phase4b-final-6827ae5/bytefray-5.0.0-py3-none-any.whl` | 1,068,017 | `94c4ec81b5428617d605db0468d360eeb0bf89b65671bc6c15302761310acb3a` |
| Sdist | `dist/phase4b-final-6827ae5/bytefray-5.0.0.tar.gz` | 975,998 | `084902725c7237da13d97b17552db32625aaeec0cb35b52b04fac8bc0ff22d11` |
| Unified exe | `dist/phase4b-final-6827ae5/windows/bytefray/bytefray.exe` | 4,272,894 | `e2af1402e4cb9fd0f85e0de05bf5f699b1e4039c378928944562b02554567892` |
| CLI exe | `dist/phase4b-final-6827ae5/windows/bytefray-cli/bytefray-cli.exe` | 2,871,078 | `688515aa4bf45d6f5f5a03bc07e73738b1bcf624f9036e98bc30dcdd2c38ec84` |
| Agent Designer exe | `dist/phase4b-final-6827ae5/windows/bytefray-agent-designer/bytefray-agent-designer.exe` | 4,266,535 | `18cc0454a14f5d709f2185c7e45713ec4d203b66464919b8267beb569ef36b7a` |
| Replay Viewer exe | `dist/phase4b-final-6827ae5/windows/bytefray-replay-viewer/bytefray-replay-viewer.exe` | 3,939,108 | `3d83defcf2e8fd21d0e7bb835f3d26b1ee52c10cd2bc0566d98e3b97e99003e8` |
| Windows installer | `dist/phase4b-final-6827ae5/installer/Bytefray-Setup-5.0.0.exe` | 101,243,431 | `13988e4330bd85105ada9fac9a42761bda4675ff72145367867bd4dc33220219` |

Every filename lists only the `.exe` itself; each PyInstaller onedir tree also
ships its full `_internal/` dependency payload at the same path (not itemized
here — the installer and the frozen-app hash above cover the whole tree it
was built from).

Byte sizes differ from Phase 3's recorded wheel/sdist sizes (1,067,857 /
975,861 bytes there vs. 1,068,017 / 975,998 bytes here) — **expected**, since
the newline fix changed `engine/src/battle_engine/replay.py`, added
`engine/tests/test_replay_newline_canonicalization.py`, and added two
documentation files, all of which are packaged in the sdist (the test file is
not, but the source and doc changes still shift the tarball). No Phase 3 hash
was reused for any Phase 4B artifact.

## 5. Package purity (Section G)

`tools/check_wheel.py` (the repository's own wheel validator) against the new
wheel: **PASS** — `Validated wheel contents:
dist\phase4b-final-6827ae5\bytefray-5.0.0-py3-none-any.whl`.

Manual inspection of both archives:

| Check | Wheel | Sdist |
|---|---|---|
| Member count | 215 (matches Phase 3/4's recorded 215 exactly) | 283 (matches Phase 3/4's recorded 283 exactly) |
| Starter manifest count | 21/21, byte-identical to the canonical list | 21/21 |
| `rc1`, `octave`, `opus`, `adversarial` substrings | none found | none found |
| `__pycache__` / `.pyc` | none found | none found |
| `ProgramData`, `C:\Users`, `/home/`, `D:\Projects` (dev-path leakage) | none found | none found |
| pMARS distribution material outside `battle_engine/pmars.py` | none (enforced by `check_wheel.py`) | n/a (sdist is source-only) |
| `write_replay()` in packaged source pins `newline="\n"` | **confirmed present** | not separately re-checked (identical source tree) |
| Version | `5.0.0` (wheel METADATA, matches filename) | `5.0.0` |

## 6. Windows wheel qualification (Section H)

Fresh venv (`wheel-env`) created outside any existing environment, verified
to resolve `battle_engine` from the venv's own `site-packages`
(`C:\Users\rasat\AppData\Local\Temp\bytefray-phase4b-qual\wheel-env\...`), not
the source checkout.

| Workflow | Result |
|---|---|
| `bytefray --version` | `Bytefray 5.0.0, Agent API v2, result schema v2, replay schema v4, Python 3.13.14` |
| `bytefray --help` / `agents --help` | PASS |
| `bytefray agents` (starter discovery) | **21/21** |
| Pairwise Ruleset-v4 match | PASS |
| 3-entrant match | PASS |
| Tournament (3 entrants) | PASS — 3/3 completed, 0 failed |
| Replay generation + headless playback | PASS |
| Starter validation (`v5_dual_team`) | PASS — `status: valid`, `api_version: 2` |
| Agent create/validate/test (`--api-version 2 --template annotated`) | PASS |
| Evaluation workflow | PASS — 6-match matrix produced |
| Exact fixed-seed regression | **PASS** — 23,171 bytes, 0 CRLF, SHA-256 `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` — exact match |

## 7. Windows sdist qualification (Section I)

Separate fresh venv (`sdist-env`), installed only from the sdist tarball
(never from the source checkout or the wheel venv).

| Check | Result |
|---|---|
| `bytefray --version` | `5.0.0` |
| Starter discovery | 21/21 |
| Pairwise match | PASS |
| Starter validation (`v5_dual_team`) | PASS |
| Exact fixed-seed regression | **PASS** — 23,171 bytes, 0 CRLF, SHA-256 `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` — identical to wheel and source |

## 8. Frozen Windows application qualification (Section J)

Against the built `dist/phase4b-final-6827ae5/windows/*` trees directly (no
installer involved at this stage), isolated `BYTEFRAY_ROOT`:

| Check | Result |
|---|---|
| Unified exe `--version` | `Bytefray 5.0.0, ...` |
| CLI exe `--help` | PASS, exit 0 |
| Agent Designer / Replay Viewer startup | PASS — already exercised unconditionally by `build_win.ps1`'s own GUI smoke (Designer, via both the unified dispatcher's `design` subcommand and the standalone binary); Replay Viewer additionally held open 5s against a real generated replay in this phase and did not exit/crash |
| Starter discovery (frozen `bytefray.exe`) | 21/21 |
| Process-share regression: default, `raider_share=0.7`, `raider_share=0.33` | PASS, all three |
| Exact fixed-seed regression (frozen `bytefray.exe`) | **PASS** — 23,171 bytes, 0 CRLF, SHA-256 `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` |

No divergence from source/wheel/sdist was observed at this tier.

## 9. Windows installer (Section K)

**Built and hashed** (§4). Compiled cleanly with Inno Setup 6.7.3 in 47.25s,
exit code 0, from the exact `dist/windows` payload verified in §8.

**Elevated install/upgrade/uninstall lifecycle: not run in this session.**
This machine's shell is not elevated, this is a non-interactive session that
cannot click a UAC consent prompt, and — per this repository's qualification
tier-honesty standard — an unreached tier must be reported as unreached, not
folded into a broader pass or worked around with a non-representative
substitute (e.g. a non-elevated dev-mode launch). The user chose, when asked,
to run this tier themselves in an elevated shell. See §14 for the exact
handoff commands prepared for that run. **This is the one Windows gate item
still open; §13's Windows gate is stated as partial pending it.**

**Update (2026-09-15, see §22 Addendum):** the user subsequently ran this
tier themselves in an elevated shell using the exact prepared handoff
command, `tools/smoke_after_install.ps1 -Lifecycle` against the isolated
`D:\Bytefray Phase4B Test\Application` / `D:\Bytefray Phase4B Test\Data`
paths from §14. Reported outcome: `Installed application smoke passed.` /
`Upgrade preserved modified agents; uninstall removed programs and retained
data.` / `=== SUCCESS: full installer lifecycle passed ===`. This is
independently corroborated by the retained `Data` tree: `Application` no
longer exists (uninstalled) while `Data\agents\user-upgrade-sentinel.txt`
(planted to prove upgrade preserves user modifications) survived. **This
tier is now PASS.**

## 10. Windows cross-form consistency (Section L)

| Form | Bytes | CRLF | SHA-256 |
|---|---|---|---|
| Source (`.venv`, editable install) | 23,171 | 0 | `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` |
| Wheel (isolated venv) | 23,171 | 0 | `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` |
| Sdist (isolated venv) | 23,171 | 0 | `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` |
| Frozen `bytefray.exe` | 23,171 | 0 | `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` |
| Installed candidate | 23,171 | 0 | `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` |

**Update (2026-09-15, see §22 Addendum):** the installed-candidate row was
completed via the elevated lifecycle run referenced in §9. All five reached
Windows forms are now byte-identical. This is the exact fixed-seed command
from the task brief (`v5_dual_team raider_share=0.7` vs `v4_quorum`,
`bytefray-rules-4`, arena 512, quota 8, ticks 30, seed 602) in every case,
independently re-verified against `D:\Bytefray Phase4B Test\Data\runs\
phase4b-installed-fixedseed.jsonl` (23,171 bytes, 0 CRLF, SHA-256 matches
exactly).

## 11. Windows gate (Section M)

**WINDOWS PHASE 4B FINAL ARTIFACT QUALIFICATION: PARTIAL — PASS ON EVERY
REACHED TIER, ONE TIER (INSTALLER LIFECYCLE) NOT YET RUN.**

Every Windows gate this session could reach — source sanity, wheel, sdist,
frozen applications, and installer *build* — passed with the exact required
hash. The installer *lifecycle* (install/upgrade/uninstall, §9) requires
elevation this session does not have; it is deferred to the user per their
explicit choice, not silently skipped or approximated. The exact wheel/sdist
were preserved unmodified for Linux transfer regardless of this open item,
per the task's Section M instruction.

**Update (2026-09-15, see §22 Addendum):** the installer lifecycle tier is
now complete (§9) and independently corroborated. **WINDOWS PHASE 4B FINAL
ARTIFACT QUALIFICATION: PASS — every Windows tier, including the installer
lifecycle, now passed with the exact required hash.**

## 12. Linux artifact transfer verification (Section O)

Transferred via WSL2 Ubuntu (this machine — see §15 for why this differs from
Phase 4's separate physical Linux machine) to `~/bytefray-phase4b/` outside
any repository checkout:

| Artifact | Windows bytes | Windows SHA-256 | Linux bytes | Linux SHA-256 | Match |
|---|---|---|---|---|---|
| Wheel | 1,068,017 | `94c4ec81b5428617d605db0468d360eeb0bf89b65671bc6c15302761310acb3a` | 1,068,017 | `94c4ec81b5428617d605db0468d360eeb0bf89b65671bc6c15302761310acb3a` | **Exact** |
| Sdist | 975,998 | `084902725c7237da13d97b17552db32625aaeec0cb35b52b04fac8bc0ff22d11` | 975,998 | `084902725c7237da13d97b17552db32625aaeec0cb35b52b04fac8bc0ff22d11` | **Exact** |

## 13. Linux environment

- Distribution: Ubuntu 24.04.3 LTS (Noble Numbat)
- Kernel: `Linux DESKTOP-JQ97S15 6.6.87.2-microsoft-standard-WSL2`
- Architecture: `x86_64`
- Platform: **WSL2**, not bare-metal — this machine, not the separate
  physical Linux machine Phase 4 used (see §15). Stated explicitly per this
  repository's tier-honesty standard rather than presented as equivalent to
  Phase 4's environment without comment.
- Python: 3.12.3 (system)
- pip: 24.0
- Qualification environments: two fresh venvs (`wheel-env`, `sdist-env`)
  under `~/bytefray-phase4b/`, entirely outside any repository checkout (this
  WSL instance has no Bytefray repo checked out at all — the strongest form
  of "cannot resolve from source checkout" available).

## 14. Linux wheel requalification (Section P)

| Workflow | Result |
|---|---|
| `battle_engine.__file__` resolution | `~/bytefray-phase4b/wheel-env/.../site-packages/...` — not a source checkout |
| `bytefray --version` | `Bytefray 5.0.0, ..., Python 3.12.3` |
| Starter discovery | 21/21, exact canonical list |
| Pairwise match | PASS |
| 3-entrant match | PASS |
| Tournament | PASS — 3/3 completed |
| Headless replay | PASS |
| Starter validation (4 Agent API v2 agents) | PASS, all `status: valid` |
| Agent create/validate/test (API v2, annotated template) | PASS |
| Evaluation workflow | PASS — 6-match matrix |
| Process-share: default, 0.7, 0.33 | PASS, all three |
| Exact fixed-seed regression | **PASS** — 23,171 bytes, 0 CRLF, SHA-256 `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` — **byte-identical to every Windows form in §10** |

## 15. Linux sdist requalification (Section Q)

Separate fresh venv (`sdist-env`), installed only from the transferred
tarball.

| Check | Result |
|---|---|
| `bytefray --version` | `5.0.0` |
| Starter discovery | 21/21 |
| Pairwise match | PASS |
| Headless replay | PASS |
| Starter validation (`v5_dual_team`) | PASS |
| Exact fixed-seed regression | **PASS** — 23,171 bytes, 0 CRLF, SHA-256 `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` |

## 16. Linux GUI smoke (Section R)

**Not run.** `docs/LINUX_INSTALL.md` and this repository's CI
(`.github/workflows/linux-gui-smoke.yml`) both establish Xvfb + a specific
xcb/EGL library set as the documented, CI-validated path — the same
precedent Phase 4 followed. This WSL2 Ubuntu instance does not have `xvfb`
or those libraries installed, and installing them requires `sudo apt-get`,
which requires a password this non-interactive session does not have and
cannot prompt for. Reported as an open item rather than skipped silently or
substituted with an unvalidated native-Wayland/offscreen run. Native Wayland
remains the documented "unvalidated" support position, unchanged by this
phase.

**Update (2026-09-15, see §22 Addendum):** re-checked independently before
closing this report. This tier is **still not run** — the WSL2 Ubuntu
instance shows no `xvfb` package, no `Xvfb`/`xvfb-run` binary anywhere on the
filesystem, and no apt/dpkg log entry ever installing it or the required xcb
library set. This is the one remaining open item in this report.

**Further update (2026-09-15, see §23):** this gate is now closed via a
native Ubuntu Wayland qualification run performed on a separate physical
laptop — not this repository's WSL2 Ubuntu instance referenced immediately
above, which remains without `xvfb` or the required Wayland/X11 GUI
libraries installed and is unchanged by this update. See §23 for the full
evidence and, per this repository's tier-honesty standard, an explicit
statement of what this session could and could not independently verify
about a run on hardware it has no access to. **This tier is now PASS.**

## 17. Cross-platform byte-identity proof (Section S)

| Form | Platform | Bytes | CRLF | SHA-256 |
|---|---|---|---|---|
| Source | Windows | 23,171 | 0 | `6deed2d6...4ae78a` |
| Wheel | Windows | 23,171 | 0 | `6deed2d6...4ae78a` |
| Sdist | Windows | 23,171 | 0 | `6deed2d6...4ae78a` |
| Frozen exe | Windows | 23,171 | 0 | `6deed2d6...4ae78a` |
| Installed | Windows | 23,171 | 0 | `6deed2d6...4ae78a` |
| Wheel | Linux (WSL2 Ubuntu 24.04.3) | 23,171 | 0 | `6deed2d6...4ae78a` |
| Sdist | Linux (WSL2 Ubuntu 24.04.3) | 23,171 | 0 | `6deed2d6...4ae78a` |

**Update (2026-09-15, see §22 Addendum):** the Windows installed-candidate
row is now complete via the elevated lifecycle run. **All seven qualified
replay forms are byte-identical**, all matching the required
`6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a`. This is
the artifact/replay-hash byte-identity proof specifically; it is independent
of the separate, still-open Linux GUI Xvfb smoke item tracked in §16 and
§22, which concerns desktop GUI startup, not replay/artifact hashes.

## 18. Closing the original Phase 4 failure (Section T)

The original Phase 4 Linux qualification (`V5_FINAL_LINUX_PACKAGE_QUALIFICATION.md`)
recorded a genuine raw-replay hash mismatch (Windows `dcf24b4e...`, Linux
`6deed2d6...`) and failed the publication gate pending root-cause
identification. That investigation is preserved unedited. Phase 4A
(`V5_FINAL_REPLAY_NEWLINE_REMEDIATION.md`) subsequently proved the mismatch
was solely CRLF-vs-LF replay serialization, fixed it with a single
`newline="\n"` pin in `write_replay()`, and qualified the fix on Windows.
This Phase 4B report is the artifact-rebuild-and-requalification step both of
those reports named as their required next gate: every reached Windows and
Linux artifact form built from the remediation commit now produces the
canonical Linux hash, not the old Windows CRLF hash — the original finding is
conclusively closed at the artifact level, pending only the installer
lifecycle's confirmation that the installed candidate matches too.

## 19. New findings

**None.** No new production defect was found in this phase. Both open items
(installer lifecycle, Linux GUI smoke) are environment/access gaps in this
session (no elevation, no `sudo` password for package installation), not
observed or suspected product defects — every check actually run, on every
reached tier and platform, passed with the exact required values.

**Update (2026-09-15, see §22 Addendum):** the installer-lifecycle gap has
since been closed by the user; Linux GUI smoke remains the one open
access/environment gap.

## 20. Handoff — remaining steps to reach the final publication gate

**Update (2026-09-15):** item A below is complete — see §9 and §22. Item B
remains open.

Two items remain before Section V's final gate can be declared:

**A. Windows installer elevated lifecycle** (requires an elevated
PowerShell on this machine):

```powershell
cd D:\Projects\BATTLE2
powershell -File tools\smoke_after_install.ps1 `
  -InstallerPath "dist\phase4b-final-6827ae5\installer\Bytefray-Setup-5.0.0.exe" `
  -AppDir "D:\Bytefray Phase4B Test\Application" `
  -DataRoot "D:\Bytefray Phase4B Test\Data" `
  -Lifecycle
```

This isolated path (distinct from `%ProgramFiles%\Bytefray` /
`%ProgramData%\Bytefray`, both of which are currently occupied by a real
installed Bytefray on this machine) runs the full install → smoke → user-data
modification → upgrade-reinstall → smoke → uninstall → removal-and-retention
verification cycle without touching that real installation. It does not by
itself run the exact `v5_dual_team raider_share=0.7` fixed-seed hash check;
after it reports `SUCCESS`, reinstall once more and run:

```powershell
& "D:\Bytefray Phase4B Test\Application\bin\bytefray\bytefray.exe" run `
  --a-type v5_dual_team --a-param raider_share=0.7 --b-type v4_quorum `
  --ruleset bytefray-rules-4 --arena 512 --quota 8 --ticks 30 --seed 602 `
  --replay "D:\Bytefray Phase4B Test\Data\fixed-seed-installed.jsonl"
Get-FileHash "D:\Bytefray Phase4B Test\Data\fixed-seed-installed.jsonl" -Algorithm SHA256
```

Required: 23,171 bytes, SHA-256
`6DEED2D65CA8BE145110037550C17592AD2AA8BD1D13B6FBD8A3D8CB554AE78A`.

Testing against the **real, currently-installed** Bytefray at the default
paths (which would exercise the literal "upgrade from currently installed
5.0.0" scenario in Section K item 1) was deliberately **not** done
automatically in this phase, since it would silently modify and then
uninstall that real installation and its real `runner\agent.yaml` as a side
effect. That remains available as an explicit, separate choice if wanted —
not performed here without asking first.

**B. Linux GUI smoke** (requires one `sudo` command in the WSL2 Ubuntu
instance, since this session has no password for it):

```bash
wsl -d Ubuntu -- sudo apt-get update
wsl -d Ubuntu -- sudo apt-get install -y --no-install-recommends \
  xvfb libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 \
  libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
  libxcb-shape0 libxcb-xinerama0 libxcb-xkb1
```

Once installed, the Designer/Replay Viewer startup smoke can be run against
the wheel venv already qualified in §14 (`~/bytefray-phase4b/wheel-env`, with
`bytefray[designer,replay]` installed) under `xvfb-run -a`.

## 21. Final publication gate (Section V)

    FINAL 5.0.0 PUBLICATION QUALIFICATION: PARTIAL —
    EVERY REACHED WINDOWS AND LINUX GATE PASSED WITH THE EXACT REQUIRED
    HASH (6DEED2D6...4AE78A) ACROSS SIX OF SEVEN ARTIFACT FORMS; WINDOWS
    INSTALLED-CANDIDATE LIFECYCLE AND LINUX GUI SMOKE REMAIN OPEN, BOTH
    ON ENVIRONMENT/ACCESS GROUNDS ONLY, NOT ON ANY OBSERVED DEFECT.

Per Section W, no tag, no GitHub release, no PyPI publication, and no
historical-artifact deletion occurred in this phase regardless of gate
state.

**Update (2026-09-15, see §22 Addendum) — superseding gate statement:**

    FINAL 5.0.0 PUBLICATION QUALIFICATION: PARTIAL —
    THE WINDOWS INSTALLER LIFECYCLE AND WINDOWS INSTALLED-CANDIDATE
    FIXED-SEED REPLAY ARE NOW COMPLETE AND INDEPENDENTLY VERIFIED, MAKING
    ALL SEVEN ARTIFACT FORMS BYTE-IDENTICAL AT THE REQUIRED HASH
    (6DEED2D6...4AE78A). LINUX GUI XVFB SMOKE REMAINS OPEN — INDEPENDENTLY
    RE-CHECKED AND STILL NOT PERFORMED ON THIS MACHINE'S ONLY AVAILABLE
    LINUX ENVIRONMENT. NOT YET READY FOR TAGGING/RELEASE PUBLICATION
    PENDING THAT ONE REMAINING ITEM.

Per Section W, no tag, no GitHub release, no PyPI publication, and no
historical-artifact deletion has occurred as of this update, regardless of
gate state.

**This PARTIAL statement was superseded on 2026-09-15 by the Linux GUI
closeout in §23; see §24 for the final gate statement.**

## 22. Addendum — independent verification of manually-completed tiers (2026-09-15)

Following this report's original PARTIAL gate, the user reported completing
the two access-gated items themselves outside this session (an elevated
PowerShell for the installer lifecycle; the WSL2/Xvfb path for Linux GUI
smoke) and asked for the gate to be closed. Per this repository's standing
rule that qualification claims are verified against real evidence rather
than accepted on report alone, each of the three items was independently
checked against artifacts actually present on this machine before this
report was updated:

| Item | Claimed | Independently verified | Result |
|---|---|---|---|
| Windows installer elevated lifecycle | PASS — install/upgrade/uninstall via `tools/smoke_after_install.ps1 -Lifecycle` | `D:\Bytefray Phase4B Test\Application` no longer exists (uninstalled); `...\Data` tree survives with `agents\user-upgrade-sentinel.txt` (content: "preserve across upgrade and uninstall") intact — consistent with "upgrade preserved modified agents; uninstall removed programs and retained data" | **CONFIRMED** |
| Windows installed-candidate fixed-seed replay | PASS — 23,171 bytes, 0 CRLF, SHA-256 `6deed2d6...4ae78a` | `D:\Bytefray Phase4B Test\Data\runs\phase4b-installed-fixedseed.jsonl`: 23,171 bytes exactly, 0 CRLF, SHA-256 `6deed2d65ca8be145110037550c17592ad2aa8bd1d13b6fbd8a3d8cb554ae78a` — exact match; adjacent `result.json` independently shows `product_version: "5.0.0"`, `ruleset_id: "bytefray-rules-4"`, seed 602, arena 512, entrants `v5_dual_team`/`v4_quorum` matching the required command exactly | **CONFIRMED** |
| Linux GUI Xvfb smoke | PASS — via the documented WSL2/Xvfb path | On the WSL2 Ubuntu instance (the same one used for §12–§15's wheel/sdist requalification): `dpkg -s xvfb` → "not installed"; no `Xvfb` or `xvfb-run` binary found anywhere on the filesystem (only unrelated `bash-completion` stub files matched); `/var/log/apt/history.log` for the current month is empty; `/var/log/dpkg.log` and its rotated predecessor contain no install entry for `xvfb` or the required `libxcb-cursor0`/`libxkbcommon-x11-0` set; no other WSL distro is registered on this machine | **NOT CONFIRMED — no evidence this tier was ever run** |

Per this repository's qualification-tier-honesty standard, a claimed result
without supporting evidence — and directly contradicted by the only
available Linux environment — is not recorded as PASS. The user, informed
of this discrepancy, chose to keep Linux GUI smoke open in this report
rather than mark it complete. The two Windows-side items are corroborated by
concrete, independently-inspected artifacts and are recorded as PASS above
(§9, §10, §11, §17, §20).

The final gate therefore remains **PARTIAL**, with Linux GUI Xvfb smoke as
the sole outstanding item, per §21's updated gate statement above. The exact
one-time command from §20 item B is still the correct next step to close it.

## 23. Native Linux Wayland GUI qualification — final closeout (2026-09-15)

The Linux GUI smoke item left open by §16/§22 has been closed, not via the
WSL2/Xvfb path those sections tracked, but via a qualification run the user
performed directly on a separate, native Ubuntu laptop
(`rod-HP-Pavilion-Notebook`) outside this session's reach.

### Environment

| Item | Value |
|---|---|
| Distribution | Ubuntu 26.04.1 LTS (Resolute Raccoon) |
| Kernel | `7.0.0-31-generic`, `x86_64` |
| Desktop | GNOME, native Wayland (not WSL2, not a container, not Xvfb) |
| Python | 3.14.4, base interpreter `/usr/bin/python3.14` |

### Artifact under test

The exact publication-candidate wheel from this report's own §4/§12:
`bytefray-5.0.0-py3-none-any.whl`, 1,068,017 bytes, SHA-256
`94c4ec81b5428617d605db0468d360eeb0bf89b65671bc6c15302761310acb3a` — installed
into a clean, dedicated venv on that laptop from the local artifact, not from
PyPI or source. `battle_engine/replay.py` was inspected inside the wheel and
confirmed to carry the post-remediation `newline="\n"` fix from commit
`314ccda`.

### Reported results

| Check | Result |
|---|---|
| `bytefray --version` | `5.0.0` |
| `bytefray --help` | PASS |
| `bytefray agents` | 21/21 expected starters |
| Agent Designer (`bytefray-agent-designer`, native Wayland) | PASS — launched under native Wayland, stable 5+ minutes, no traceback/error output, deliberate SIGTERM exit 143 |
| Replay Viewer (`bytefray replay --renderer pygame`, replay generated on the installed wheel: writer vs runner, 200 ticks) | PASS — opened successfully, stable for the full hold interval, only the expected pygame-ce startup banner printed, deliberate SIGTERM exit observed cleanly |

**Native Ubuntu Wayland GUI smoke: PASS.**

### Qualification-environment observations (not product defects)

1. An initial metadata check run from inside the BATTLE2 source checkout on
   that laptop reported `4.0.0rc2`, because the checkout's `bytefray.egg-info`
   shadowed the clean venv install through `sys.path[0]`. Re-running outside
   the repository with a sanitized import environment correctly showed
   Bytefray 5.0.0 from the qualification venv. This is a checkout/`sys.path`
   ordering artifact of running a metadata check from inside a repo that also
   has an editable/egg-info install nearby, not a packaging defect.
2. An intentionally over-sanitized GUI environment with `DISPLAY` and
   `WAYLAND_DISPLAY` removed caused Qt platform initialization to fail, as
   expected for any Qt application with no display backend selected.
   Restoring the actual native desktop environment allowed Agent Designer to
   run normally under Wayland.
3. Screenshots were not captured, because GNOME screenshot facilities were
   unavailable to the automation environment on that laptop. Screenshots were
   optional for this gate and their absence does not affect the result.
4. Deep menu/click UX automation (the kind of checklist in
   `docs/MANUAL_SMOKE_TESTS.md`) was not performed and remains a separate,
   still-open manual item. The requested and delivered qualification here was
   startup/runtime/replay smoke, not full UX certification.

### This session's verification boundary

This session runs on a Windows machine with no access to the reported native
Ubuntu laptop — no shell, no filesystem, no way to independently execute or
observe the commands above, unlike the WSL2 checks in §16/§22, which this
session could and did inspect directly (and found not confirmed). Per this
repository's qualification-tier-honesty standard, that distinction is
recorded explicitly rather than presented as if this session had witnessed
the run itself:

| Item | Basis |
|---|---|
| Wheel identity (1,068,017 bytes, SHA-256 `94c4ec81...`) | **Independently reconfirmed by this session** — recomputed directly against `dist/phase4b-final-6827ae5/bytefray-5.0.0-py3-none-any.whl`, still present on this machine from §3's build: exact match. This is the same wheel already proven byte-identical between Windows and WSL2-transferred Linux in §12. |
| `replay.py` `newline="\n"` fix present at `FINAL_SOURCE_SHA` | **Independently reconfirmed by this session** — inspected directly via `git show 6827ae5:engine/src/battle_engine/replay.py`. |
| Agent Designer / Replay Viewer native-Wayland startup, stability, and clean exit | **Reported by the user; not independently witnessed by this session** — no local artifact (log, screenshot, exit-code capture) exists for this session to inspect, unlike the Windows installer-lifecycle claim in §22, which had a filesystem trace this session could check. |

Given no contradicting evidence exists (unlike the WSL2 claim §22 refuted)
and the artifact identity itself is independently confirmed, this report
records the gate as closed on the user's direct, first-hand account of a run
they performed themselves — while distinguishing that from the tiers this
session verified against its own tool access. Readers relying on this report
for further release decisions should treat the GUI-behavior row above as
user-reported, not session-witnessed.

## 24. Final publication gate — closeout (2026-09-15)

    FINAL 5.0.0 PUBLICATION QUALIFICATION PASSED —
    READY FOR RELEASE PUBLICATION

Every final publication gate has now passed: Windows source qualification,
Windows wheel, Windows sdist, Windows frozen candidate, Windows installed
candidate, Windows installer lifecycle, Linux wheel, Linux sdist, canonical
replay determinism (23,171 bytes, 0 CRLF, SHA-256
`6DEED2D65CA8BE145110037550C17592AD2AA8BD1D13B6FBD8A3D8CB554AE78A`), and
native Linux (Ubuntu 26.04.1 LTS, GNOME, native Wayland) Agent Designer and
Replay Viewer smoke per §23. The artifact identity and source fix underlying
§23's evidence are independently confirmed by this session; the GUI runtime
behavior itself is recorded as the user's first-hand report from hardware
this session has no access to, per §23's verification-boundary table.

The `v5.0.0` tag (`6827ae58d969ddbe483f3601749bb78014aa2c5f`) already exists
and is unaffected by this documentation update; nothing in this update
implies tagging still needs to happen. Per Section W, no GitHub release, no
PyPI publication, and no historical-artifact deletion has occurred as of
this report. Remaining publication work is administrative only:

- generate `SHA256SUMS` from the exact Phase 4B public artifacts;
- create the GitHub Release for the existing `v5.0.0` tag;
- upload the exact qualified artifacts;
- verify uploaded hashes against this report's recorded values;
- optionally establish PyPI publication separately.

Given no contradicting evidence exists (unlike the WSL2 claim §22 refuted)
and the artifact identity itself is independently confirmed, this report
records the gate as closed on the user's direct, first-hand account of a run
they performed themselves — while distinguishing that from the tiers this
session verified against its own tool access. Readers relying on this report
for further release decisions should treat the GUI-behavior row above as
user-reported, not session-witnessed.
