# Bytefray 5.1.0-alpha.1 — Windows Installer Creation and Qualification

**Task:** Bytefray 5.1 Alpha — Windows Installer Creation and Qualification (authorized by the project lead on 2026-10-20)

**Release worktree:** `D:\Projects\BATTLE2-worktrees\5_1_alpha1_windows`

**Release branch:** `release/5.1.0-alpha.1-windows-candidate` (local, unpushed)

**Base commit:** `0a962a3fe9f75ec8ab07741ef38c2eb07e1f2e7d` (`0a962a3`, accepted P2 Remediation 03)

**Candidate commit (installer source):** `5e835290166d5c3fd870eaba221daf81d85b49c0` (`5e83529`). This report is committed on top of it as a documentation-only commit; nothing it changes ships in the installer.

**Bundled Spectator:** Bytefray Spectator `0.1.0-alpha.1`, source `libertaine/Bytefray-Spectator` `designer-integration` at `14089a7bf624a5974346306a277e307ea8f48c07`. `bytefray-spectator.exe` is 137,850,648 bytes, SHA-256 `8a3bd1a48430a0edd1faf8ca5c5b287ed1ecd06975c4e683f273562d428fd602`.

**Installer:** `Bytefray-5.1.0-alpha.1-Windows-x64-Setup.exe`, 113,834,819 bytes, SHA-256 `4f964117103c114cdd1b9ac291ead76ca35fa4b9d8bd0c2903bcf0651bfac2f9`. It is **not code-signed** and has not been submitted to Microsoft.

**Result:** **READY WITH CONDITIONS — PROJECT LEAD DECISION REQUIRED.** The final installer passes all 161 checks of its installed qualification (§F), including the guard scenarios from six review rounds. The full suite matches the 89-failure baseline node for node, and the independent review (round 6) is **PASS WITH CONDITIONS**. Publication conditions are in §I.

Evidence lives outside the repository under `D:\Projects\Bytefray-release-candidates\5.1.0-alpha.1-windows\`. That folder holds:

- `artifacts\`: the installer and `SHA256SUMS`.
- `evidence\`: build and compiler logs, qualification logs and results, screenshots, full-suite JUnit files, review briefs and reports, and protected-checkout snapshots.
- `build-<sha>\`: the clean source exports each candidate was built from.

---

## A. Packaging audit and build plan

**Starting point.** `0a962a3` was present locally, and its worktree `p2-remediation-03-launcher` was clean. The new worktree and branch were created from it with `git worktree add -b release/5.1.0-alpha.1-windows-candidate`. No pre-existing worktree was used or modified. Full-suite and GUI-split runs used helper worktrees created for this task (§I).

**Bytefray 5.0's installer, inspected before anything was designed.**

- `AppId {A5B86D38-9A6C-4D7F-9B4E-BA7720000002}`, a per-machine installation into `C:\Program Files\Bytefray`, with data in `C:\ProgramData\Bytefray`.
- It sets `BYTEFRAY_ROOT` machine-wide and removes it on uninstall.
- Any installer reusing that AppId, those folders or that variable could upgrade over, uninstall or redirect 5.0.

On this machine an unregistered `C:\Program Files\Bytefray` tree (736 files) and `C:\ProgramData\Bytefray` (560 files) exist. Bytefray 5.0 is **not registered**. Both trees were hash-snapshotted before and after and never written.

**Gaps found in the existing Windows packaging, and the plan.**

| Area | As found at `0a962a3` | Plan (implemented) |
|---|---|---|
| Product identity | 5.0's AppId, per-machine, `BYTEFRAY_ROOT` | New AppId `{30F5713B-F69B-44F1-A759-AC43E33C0889}`, `PrivilegesRequired=lowest`, its own folders, Start Menu group and uninstall entry. No HKLM write, no environment variable |
| Data root in frozen builds | Inherited `BYTEFRAY_ROOT` (5.0's machine-wide value would redirect the Alpha) | Installation record `bin\bytefray-install.json` written by Setup. PyInstaller runtime hook `tools/pyi_rth_bytefray_install.py` makes every frozen executable use it |
| Spectator | Not packaged | Pinned build staged at `bin\bytefray-spectator\`, found by Designer after `BYTEFRAY_SPECTATOR` and before the data-root drop-in and `PATH` |
| Versions | `5.0.0`; no Windows version resources | `5.1.0a1` / `5.1.0-alpha.1`; version resources `5.1.0.101` |
| Licenses | No third-party notices | `licenses\` from the build environment and recorded upstream texts |
| Dependencies | Unpinned | `tools/windows-build-constraints.txt` (exact pins, including the isolated build backend) |
| Unused Qt | Qt Virtual Keyboard (GPL-3.0-only) and the Quick/QML/OpenGL/PDF libraries it and the PDF image plugin pull in | Omitted after PyInstaller. The build fails if any remaining binary imports (or delay-imports) them |

## B. Version update

Following `docs/COMPONENT_VERSIONING.md`:

| Item | Value |
|---|---|
| Python package (`pyproject.toml`) | `5.1.0a1`; `result.json` `product_version` stays PEP 440 |
| Public version | `5.1.0-alpha.1` (`battle_engine.project_info.public_version()`); `bytefray --version` and About show `5.1.0-alpha.1 (package 5.1.0a1)` |
| Windows file version | `5.1.0.101` (`tools/windows_version_info.py`, checked against every executable by the build) |
| Installer | `AppVersion=5.1.0-alpha.1`, `VersionInfoVersion=5.1.0.101`, file name `Bytefray-5.1.0-alpha.1-Windows-x64-Setup.exe` |
| Component identities | Unchanged: Ruleset IDs (`bytefray-rules-4` default, `bytefray-rules-6-alpha1`), Agent API v2, result schema v2, replay schema v4, presentation manifest versions, starters |
| Compatibility record | `proposed` → `candidate`; the checker requires a candidate's version to equal `pyproject.toml` and its Spectator entry to equal `tools/spectator_companion.json` |
| Spectator | Keeps its own version `0.1.0-alpha.1`; not derived from Bytefray's |

The pinned version tests were updated with the version, not weakened. `test_version_transition_5_1_0_alpha_1` replaces `test_version_transition_5_0_0`, and the record test that required `proposed` now requires `candidate`, with negative controls.

## C. Frozen executables and frozen Spectator CLI

**Applications.** Four PyInstaller 6.22.2 onedir trees are built from `tools/*.spec`: `bytefray`, `bytefray-cli`, `bytefray-agent-designer` and `bytefray-replay-viewer`. Each carries the install-record runtime hook and a version resource.

**Build-time smoke (`tools/build_win.ps1`; fails the build).**

- Python bytecode and caches are absent from the payload, and the unused Qt files are proven absent and unreferenced.
- Version resources match.
- `agents create` runs for all five scaffold templates. The three sensing copies are refused under Classic (exit 2) and accepted under Active Sensing.
- The pinned Spectator runs `--headless -- --fixture=sample --check`.
- `bytefray run` (Active Sensing), then `bytefray spectator export`, `verify` and `prepare` twice (`reused` false, then true). These run with redirected output in a data root containing spaces and `Ω`.

**Installed CLI (fresh default-folder install of the final installer, 54/54 PASS, `evidence\qual-5e83529\cli\`).**

- Version, help and legacy-help:
  - `bytefray --version` → `Bytefray 5.1.0-alpha.1 (package 5.1.0a1), Agent API v2, result schema v2, replay schema v4, Python 3.13.14`.
  - `--help` for the root, `spectator`, `spectator export/prepare/verify`, `agents` and `run`; `bytefray-cli --help`; replay viewer `--help`.
- Data root and agents:
  - The recorded data root wins over a decoy `BYTEFRAY_ROOT`, which stays empty.
  - Personal copies of all three teaching agents are refused by Classic and accepted by Active Sensing.
- Matches and replay: Classic, Active Sensing two-entrant, three-entrant, and headless replay.
- Spectator CLI, in folders whose names contain spaces and `Ω`:
  - `spectator export` (41.2 s) and `verify`.
  - Export without `--replace` is refused.
  - `prepare` runs cold (42.6 s) and then cached (`reused=true`, 0.59 s).
  - Classic, three-entrant and tampered replays are refused with stable codes (`unsupported_ruleset`, `unsupported_roster`, `result_unverified`).
  - `bytefray-spectator.exe --check` on the export prints `PRESENTATION OK … manifest version 2`.
- No process is left running from the install folder.

**Defect found and fixed here (b95be54).** Under a data root whose path is not representable in the console code page (cp1252), Designer's Development Test left **Open Replay** disabled. Child-command output reached Designer in cp1252 with the replay path escaped. The fix has three parts:

- `bytefray` applies `PYTHONIOENCODING` itself, since the frozen interpreter ignores it.
- Designer sets `PYTHONIOENCODING=utf-8` for its children.
- Designer decodes their output incrementally as UTF-8.

The frozen GUI flow passed afterwards.

## D. Spectator bundling and discovery

- **Build.** The Spectator source repository was used read-only. A clean clone at `14089a7` was exported with Godot 4.7.2 (official Windows template, SHA-512 recorded) via `packaging/build.ps1 -Platform Windows`.
  - Godot exports are not byte-reproducible. The clean-clone build (`8a3bd1a4…`) and the integration checkout's earlier build (`98a68f5b…`) embed `.pck` files whose 50 entries are identical except a generated scene export and `uid_cache.bin` (`evidence\spectator-pck-compare.txt`).
  - The clean-clone build is the one pinned and shipped.
- **Pin.** `tools/spectator_companion.json` records the version, source commit, Godot template, build command, size, SHA-256, license hash and the manifest versions read (1, 2).
  - `build_win.ps1 -SpectatorExe` refuses any other executable.
  - The pin's record ships beside it as `SPECTATOR_BUILD.json`.
- **Discovery** (`app/services/spectator_viewer.py`, `docs/specs/spectator_export.md`), in order:
  1. `BYTEFRAY_SPECTATOR` (`off` or a path).
  2. The bundled companion `<install>\bin\bytefray-spectator\`, for frozen builds only.
  3. `<data root>\spectator\`.
  4. `PATH`.
- **Installed behavior.** View Last Match on a two-agent Active Sensing match opens the bundled executable with `--perspective=broadcast`. Broadcast and Agent A work. Closing exits 0, and reopening uses the cache (§F).
  - Fallbacks to the Pygame viewer were qualified on the earlier candidate installs and are unchanged in application code since `b95be54`: Classic, three entrants, Replay History, `BYTEFRAY_SPECTATOR=off`, bundled Spectator missing, and exporter missing (one "Spectator Unavailable" warning).
  - An override path is honored.

## E. Inno Setup installer, side by side with Bytefray 5.0

`tools/installer.iss` (Inno Setup 6.7.3, `x64os`, `lzma2` solid):

| Property | Bytefray 5.1 Alpha | Bytefray 5.0 |
|---|---|---|
| AppId | `{30F5713B-F69B-44F1-A759-AC43E33C0889}` | `{A5B86D38-9A6C-4D7F-9B4E-BA7720000002}` |
| Scope | Per user, no elevation | Per machine |
| Programs | `%LOCALAPPDATA%\Programs\Bytefray 5.1 Alpha` | `C:\Program Files\Bytefray` |
| Data | `%LOCALAPPDATA%\Bytefray 5.1 Alpha` (or `/BYTEFRAYDATAROOT=`), recorded in `bin\bytefray-install.json` | `C:\ProgramData\Bytefray` via `BYTEFRAY_ROOT` |
| Start Menu / uninstall entry | **Bytefray 5.1 Alpha** (HKCU) | **Bytefray** |
| Environment, HKLM | Never written; 5.0's uninstall key is only read, to refuse its folder | Writes `BYTEFRAY_ROOT` |

**Safety properties** (each was required by a review finding in §H, and each is exercised by §F).

- **Foreign installations.** Setup refuses a folder that holds another installation, on every run, upgrades included:
  - an uninstaller whose log is not this AppId's;
  - Bytefray program folders without this AppId's own registered, logged installation;
  - any overlap with Bytefray 5.0's registered folder.

  A leftover installation record proves nothing. A registered location counts only when the folder's uninstall logs carry this AppId.
- **Data folder.** Setup refuses a data folder inside the program folder, or containing it, comparing final paths (8.3 names, junctions and symbolic links resolved). The installed applications repeat the check with fully resolved paths and refuse to start when the record is missing or the folders overlap.
- **Links.** Setup and the uninstaller refuse to run while a junction or symbolic link exists under `bin`, `docs` or `licenses`, so neither writes nor deletes through one.
  - Each path is examined by name with `GetFileAttributesW`, which needs no right to list its parent.
  - Anything that exists but cannot be examined, or a folder that cannot be listed, is treated as a link, since an incomplete scan proves nothing.
  - Errors in the middle of a folder listing are indistinguishable from its end; listing permission is checked when the folder is opened, so an ACL cannot cause one.
- **Downgrades.** Setup records its numeric build (`5.1.0.101`) with the uninstall entry. It refuses to install over a higher recorded build, so this build's cleanup can never act on a newer build's files.
- **Installation record.** Setup deletes the old record's directory entry before writing a new one, so a hard link in its place cannot carry the record into another file.
- **Uninstall ownership.** The uninstaller deletes logged paths under the recorded folder. It therefore refuses unless that folder still holds this installation: the installed-file list must have the SHA-256 recorded with the uninstall entry, and the folder must not be reached through a link it cannot follow.
  - A moved, substituted or redirected folder therefore keeps its files, and the message says to repair with the installer, then uninstall.
  - This is a content check, not proof of identity: a deliberately planted copy of the list would pass. That is outside the actor model in §H.
  - The uninstaller keeps its own uninstall log open, so it cannot read that log. The first attempt, `33999c1`, tried to, and refused every uninstall.
- **Links Setup cannot follow.** Inno Setup 6.7 enables Windows **RedirectionGuard**, under which Setup does not follow junctions created without administrator rights (`Error 448: … untrusted mount point`). Qualification of `ef288c4` showed that a folder comparison through such a link silently used the unresolved path (§F). Setup therefore refuses, before any other check, an installation or data folder any of whose components is a link it cannot resolve. Links it can follow are resolved and compared.
- **Upgrades.** There is no `[InstallDelete]` and nothing is deleted recursively.
  - `bin\bytefray-files.txt` lists every installed file with its SHA-256 and is installed last. Its hash is kept with the uninstall entry.
  - After a later build has installed its files, Setup deletes a previous-build file only when all of these hold:
    - the vouched-for previous list names it;
    - it lies in one of the folders `[Files]` installs (never the record or the list);
    - the new build no longer ships it;
    - it is unchanged;
    - it is reached at exactly its listed path.
  - An upgrade interrupted before its files are in place has deleted nothing, and re-running completes it.
  - **Not covered in this build (a condition for the next installer).** If an upgrade is interrupted after its files are installed, or an obsolete file cannot be deleted, that file's pending removal is not retried. A later uninstall still removes it. This cannot affect 5.1.0-alpha.1 itself: no earlier build of this AppId has been published, so on users' machines its cleanup only ever compares its own list with itself.
- **Uninstall.** It removes what Setup installed, plus the record. It keeps the data folder and anything else in the program folder.

**Documents installed** to `{app}\docs`: `README.md`, `LICENSE`, `CHANGELOG.md`, the release notes, and the compatibility record (`.md` and `.json`). The notices go to `{app}\licenses`.

**Path length.** The deepest installed file is 107 characters below the installation folder. Folders longer than about 150 characters exceed the 260-character Windows limit. A first installation then stops and rolls back cleanly (observed). This is documented as a limitation.

## F. Installed-application qualification

**Environment.**

- Windows 11 Pro 10.0.26120 (x64), the developer's own account, **not elevated**.
- **No clean machine, VM, Windows Sandbox or second account was available.** This is therefore not clean-machine qualification.
- Isolation instead:
  - per-user installs, either into the default folders (which did not exist before this work) or into disposable folders under the evidence tree, some with spaces and non-ASCII names;
  - the user's registered environment only (no venv, `PYTHONPATH`, Godot or `BYTEFRAY_*`);
  - a decoy `BYTEFRAY_ROOT` simulating 5.0;
  - the protected 5.0 trees hash-snapshotted.
- Every check ran against installed, frozen executables launched as a user would: the Start Menu shortcut through the shell, or the installed `.exe`. None ran in source mode.

**Final installer (`5e83529`, SHA-256 `4f964117…c2f9`): every check passes, 161 in all, plus 54 for setting up the previous build.** Counts come from each run's results file. Evidence is in `evidence\qual-5e83529\`.

| Run, in order | Result | Evidence |
|---|---|---|
| Safety guards, disposable folders on C: (8.3 names available, one folder named with `Ω`) | **35/35 PASS** (details below) | `guards\` |
| Previous build: the `ca3362a` installer, fresh at the default folders, with its CLI run creating user data | 54/54 PASS (set-up for the next row) | `previous-ca3362a-cli\` |
| Upgrade `ca3362a` → `5e83529` with Designer open, then the same installer again with the edited list made trusted | **16/16 PASS** (details below) | `upgrade-from-ca3362a\` |
| Uninstall of that installation | **11/11 PASS** (details below) | `uninstall-after-upgrade\` |
| Fresh default-folder install + CLI | **54/54 PASS** (§C) | `cli\` |
| GUI from the Start Menu | **18/18 PASS** (details below) | `gui\` |
| Repair upgrade over the same build (edited list, untrusted then trusted) | **16/16 PASS**, as for the cross-build upgrade | `upgrade-repair\` |
| Final uninstall | **11/11 PASS** | `uninstall-final\` |

**Safety guards.** Each refusal is exit 7 with Setup's message, and nothing changed:

- A Bytefray 5.0-like folder is refused, and so is a tree with a stray installation record.
- An 8.3-alias data folder inside the program folder is refused.
- A data folder later made a junction into the program folder:
  - `bytefray.exe` and Designer refuse at runtime;
  - the following upgrade is refused by Setup, the round-2 scenario.
- A dangling-junction data folder is refused.
- A missing record is refused at runtime.
- `docs` replaced by a junction to the data folder: both upgrade and uninstall are refused, and the user's same-named README is untouched. Uninstall completes once the link is removed.
- A registered folder redirected to a 5.0-like installation is refused, and that installation is unchanged.
- **Hard link.** The record was replaced by a hard link to a user's file in the data folder. After a repair, the user's file is byte-identical and the record holds the correct data root.
- **Unlistable folder.** With directory listing denied on `_internal\PySide6`, both upgrade and uninstall are refused ("cannot be listed"). Once listing is allowed again, uninstall completes.
- **Moved installation.** The installation folder was moved away and its path replaced, first by a plain user folder, then by a junction to one. The genuine uninstaller, run from the moved tree, refuses both ("no longer holds this … installation"), and the user's files are unchanged. Moved back, it uninstalls.
- **Unlistable installation folder.** Listing was denied on the installation folder itself (not inherited; the run confirms it could not be listed), with `docs` replaced by a junction to a user's folder.
  - Setup refuses. The uninstaller finds the `docs` link by name and refuses, and the user's README is unchanged.
  - With listing allowed and the link removed, uninstall completes.
- **Downgrade.** The installed build is recorded as `5.1.0.101`. With `5.1.0.201` recorded instead, Setup refuses ("A newer Bytefray 5.1 Alpha build (5.1.0.201) is installed …") and leaves the installation unchanged.

The uninstall logs confirm that each refusal came from its intended check.

**Upgrade `ca3362a` → `5e83529`.**

- Restart Manager closed Designer.
- The data root was reused, and every data file was intact.
- With the edited list not vouched for, nothing listed was deleted.
- With the list trusted, only the obsolete, unchanged files were deleted, together with the folder they left empty. These were kept:
  - a listed file the user had changed;
  - a listed 8.3 alias;
  - climbing, absolute and rooted entries;
  - unlisted files and data inside the program folder.
- Afterwards all 705 files are byte-identical to the build. The only extras are the uninstaller pair, the record, the list, and the planted user note.

**Uninstall.** Programs, shortcuts and the HKCU entry are removed. The data root (52 files) and an unowned file are kept. Sibling folders are unchanged, and no `BYTEFRAY_ROOT` is set.

**Fresh install.** All 705 files are byte-identical to the build. The installed list is identical to the build's. The uninstall entry records its SHA-256 and the build `5.1.0.101`.

**GUI.**

- 106 loaded modules, none from outside the install folder or Windows. No startup warnings.
- Classic is the default. The three teaching starters are present. About shows `5.1.0-alpha.1 (package 5.1.0a1)`.
- Active Sensing match → View Last Match → the bundled Spectator (14.8 s cold, GUI max UIA round-trip 4 ms).
  - Broadcast, then Agent A at tick 4 (verified in the capture), then Broadcast with play/pause. Close exits 0, and a cached reopen takes 1.28 s.
- A Classic match opens in the Pygame viewer.
- Development Test of a CLI-created personal copy → Open Replay → Spectator.
- Designer exits 0, leaving no processes.

**Earlier candidates.** Application code is unchanged since `b95be54`, so these still describe the shipped applications.

- **`6aa5bed` → `b95be54`.** GUI flows from the Start Menu:
  - Classic default everywhere; About.
  - Active Sensing match → Spectator in 1.9 s (prewarmed), Broadcast/Agent A, seek/play; reopen cached 1.59 s.
  - Cold 600-tick preparation in 50.5 s with the GUI responsive (max UIA round-trip 11 ms).
  - Closing Designer mid-preparation kills the child.
  - Every Pygame fallback (§D); GUI New Agent personal copy; capability gating.
  - CLI 51/53 at `6aa5bed`, the 2 failures being harness defects that passed when rerun. Upgrade 9/9 and uninstall 11/11 at `b95be54`.
- **`e8e5018`.**
  - CLI: 59 PASS.
  - Guards:
    - a fake 5.0 folder refused;
    - an 8.3-alias data root refused on C:;
    - a junction data root refused at runtime;
    - a missing record refused.
  - The MAX_PATH rollback was observed (a first install into a too-deep folder exited 5 and rolled back cleanly). GUI 16/18 at first; the 2 failures were harness defects that passed when redone (`gui\harness-corrections.md`).
- **`1af7b2a`.** Upgrade 11/11, uninstall 11/11, fresh CLI 54/54, 705/705 files byte-identical.
- **`ef288c4`.** Upgrade 16/16, uninstall 11/11 (twice), CLI 54/54, GUI 18/18, repair 16/16; guards 16/17.
  - The guard failure: `b3.junction-upgrade-refused`. Under RedirectionGuard, Setup could not resolve the junction and the upgrade went ahead. Nothing was written or deleted through the link.
  - The redirected-folder case ended in a fatal exit 4 rather than a refusal.
  - Both were corrected in `7b94790` (§E, §G).
- **`7b94790`.** Guards 17/17, upgrade 16/16, uninstall 11/11 (twice), CLI 54/54, GUI 18/18, repair 16/16.
- **`33999c1`.** Guards 21/28.
  - Every uninstall was refused: the new ownership check read the uninstall log, which the uninstaller holds open.
  - The refusal checks passed, but for that wrong reason.
  - Corrected in `ca3362a`. The five test installations left behind were removed by hand after confirming they held only installed files. The registered one was repaired with the `ca3362a` installer and then uninstalled, the recovery path the new message gives (`evidence\qual-33999c1\recovery\`).
- **`ca3362a`.** Guards 28/28, upgrade 16/16, uninstall 11/11 (twice), CLI 54/54, GUI 18/18, repair 16/16.

**Harness corrections** (none changed a product result; each is recorded with its evidence):

- shortcut-target encoding (WScript.Shell → Shell.Application);
- `Start-Process` argument quoting;
- a comment swallowing parameters;
- UI Automation Invoke blocking on modal dialogs, so clicks are used instead;
- Qt combo boxes ignoring UIA selection;
- Spectator positions that depend on window size, now computed from Godot's stretch settings;
- `View Last Match` needing a prior match;
- the expected `bin\` listing after the file list was added.

## G. Packaging corrections and regression

**Corrections made during this task**, all local commits on the release branch:

| Commit | Correction |
|---|---|
| `16bb5cd` | Packaging, version, installer, Spectator bundling, notices, pins, smoke tests; `bytefray` escapes unencodable characters on redirected Windows streams |
| `6aa5bed` | Omit the GPL-3.0-only Qt Virtual Keyboard and the Qt Quick/QML/OpenGL/PDF libraries only it and the PDF image plugin needed (Qt payload 128 MB → 108 MB); import closure enforced |
| `b95be54` | Non-ANSI paths survive child-command output (§C) |
| `e8e5018` | Review round 1: complete notices (SDL family, WavPack, libxmp, FreeType/HarfBuzz, Qt and Mesa attributions); LGPL corresponding-source map; foreign-folder refusal; missing-record refusal; 8.3-alias comparison; compatibility JSON shipped; Tab not advertised; pins applied by the build |
| `4c7d445` | Review round 2: no recursive upgrade deletion (manifest-based); junction/symlink resolution; no record exemption; isolated build backend pinned; delay imports scanned |
| `1af7b2a` | Documented limitations found in qualification (path length, generic refusal dialog, unnamed entrant C selector) |
| `ef288c4` | Review round 3: hash-verified, post-install, integrity-checked obsolete-file cleanup; link refusal for Setup and the uninstaller; ownership by uninstall log; foreign checks on every run; a Linux-safe test |
| `7b94790` | Qualification of `ef288c4`: refuse installation and data folders reached through links Setup cannot follow (Windows RedirectionGuard) |
| `33999c1` | Review round 4: replace the record's directory entry (hard links); uninstaller ownership check; unlistable folders refused; cleanup limited to the installed trees; exact uninstall-log header |
| `ca3362a` | Qualification of `33999c1`: the uninstaller verifies its folder through the recorded installed-file list, not its own (locked) log |
| `5e83529` | Review round 5: link candidates examined by name (no parent listing needed), unexaminable paths refused; installing over a newer build refused |

No gameplay, ruleset semantics, frozen research code, replay protocol or presentation schema was changed. 5.1 functionality was not expanded. Application and engine source changes since `0a962a3` are confined to four files:

- `app/agent_designer.py`: the About version, and UTF-8 decoding of child output.
- `app/services/spectator_viewer.py`: bundled-Spectator discovery.
- `engine/src/battle_engine/command.py`: the version string, and output-stream encoding.
- `engine/src/battle_engine/project_info.py`: the public version spelling.

Everything else is packaging, tooling, tests and documentation.

**Regression.**

| Suite | Commit | Result |
|---|---|---|
| Full headless suite | `6aa5bed` | 86 failed + 3 errors = **89 inherited**, node-for-node identical to the accepted baseline `040a709`; 9,049 passed; 56 added, all passing; 2 removed (the replaced version and record tests) |
| Full headless suite | `b95be54` | 89 inherited, identical to `040a709` and `6aa5bed`; 9,053 passed; 0 changed outcomes |
| Full headless suite | `7b94790` | 86 failed + 3 errors = **89 inherited**, node-for-node identical to `040a709` and `b95be54`; 0 changed outcomes; 9,069 passed; 76 added since `040a709`, all passing; 2 removed relative to `b95be54`, both replaced by renamed tests during the review fixes (`evidence\full\compare_7b94790_vs_040a709_b95be54.txt`) |
| Designer GUI split (offscreen + native M1-5) | `b95be54` | 445 + 96 + 36 + 13 + 8 passed |
| Spectator-integration suite | `b95be54` | 68 passed |
| Targeted packaging/installer tests (installer, build steps, install record, packaging spec, compatibility record, version, notices, Spectator discovery) | `5e83529` | 163 passed, 1 skipped (POSIX-only); ruff clean; mypy clean on the new tools; compatibility record `--check` clean |

From `7b94790` to the final `5e83529`, the only Python file changed is `engine/tests/test_windows_installer_side_by_side.py`, which is in the targeted set above. The other changes are `tools/installer.iss` and documentation, none of which the suite imports, so the `7b94790` full run stands for the final code.

The 89 inherited failures are unchanged and not concealed. No test was rewritten to hide one. `app/`, `client/`, `engine/src/` and the root `tests/` are unchanged since `b95be54`, so the GUI split and Spectator suite there cover the shipped application code.

## H. Independent review

OpenAI Codex (`codex exec -s read-only`, stdin from a brief, output retained, a hard time limit) reviewed each candidate in a push-disabled clone. Briefs, reports and full transcripts are in `evidence\review\`.

| Round | Candidate | Verdict | Findings |
|---|---|---|---|
| 1 | `b95be54` | HOLD | 3 BLOCKER (missing notices; LGPL corresponding source; aliased overlapping folders), 3 MAJOR, 2 MINOR, 2 NOTE |
| 2 | `e8e5018` | HOLD | 1 BLOCKER (recursive upgrade cleanup before the runtime check), 1 MAJOR (record exemption), 2 MINOR, 1 NOTE |
| 3 | `1af7b2a` | HOLD | 1 BLOCKER (deletion through redirected parents or an edited list), 3 MAJOR (redirected registered location; cleanup outside rollback; Linux-only test failure), 2 NOTE |
| 4 | `7b94790` | HOLD | 4 MAJOR, source-derived: R4-1 record rewritten through a hard link; R4-2 uninstall under a later-redirected followable root; R4-3 cleanup retry state lost after an interrupted or failed cleanup; R4-4 an unlistable folder taken as link-free. NOTE: deliberate list-plus-registry forgery is outside the security boundary |
| 5 | `ca3362a` | HOLD | R4-1, R4-2 (original reproduction) and the NOTE resolved; R4-3 accepted as a first-publication condition. 1 MAJOR, R5-1: the link scan's initial lookup used a parent-folder search, so an unlistable installation folder hid `docs`/`bin`/`licenses` from it. NOTE: the list hash is a content witness, not identity |
| 6 | `5e83529` | **PASS WITH CONDITIONS** | R5-1 resolved, supported by the `rootlist` run. R4-1, R4-2 (original reproduction), R4-4 (static ACL cases) and the downgrade caveat resolved. No BLOCKER, MAJOR or MINOR in the delta. 2 NOTE: downgrade protection relies on future builds keeping the version registration and raising the numeric version; mid-enumeration I/O errors remain indistinguishable from the end of a listing |

**Actor model (stated by the reviewer in rounds 5–6 and applied to every disposition).** It includes ordinary installation, repair and uninstall; accidental or static folder movement; hard links; restrictive ACLs; and pre-existing links that Windows lets Setup follow. It excludes deliberate forgery of the ownership witness (list plus registry), malicious concurrent filesystem mutation, and a hostile administrator. This per-user installer grants no authority to an actor who already controls its files and its HKCU registration.

**Dispositions.** Every BLOCKER and MAJOR from rounds 1–5 was corrected, with two exceptions, both accepted by the reviewer:

- **R4-3, cleanup retry state.** Accepted as a first-publication condition. It does not affect 5.1.0-alpha.1 itself (§E) and is a gate for the next installer.
- **Round 1 B2, LGPL corresponding source.** Remains a publication condition (§I).

Each correction is listed in §G, and the installed evidence for each is in §F. Round-6 conditions, carried into §I:

- this report;
- corresponding-source delivery;
- publishing the checksum of the exact reviewed binary;
- R4-3 and the numeric-version protocol for the next installer;
- the accepted limits: enumeration errors, followable root links (source-verified only), unsigned distribution, and the single qualification environment.

The reviewer did not run installers or tests and did not hash the binary independently. Every installed result in this report comes from the qualification runs in §F.

## I. Provenance, artifact inventory, conditions and recommendation

**Build provenance.**

| Item | Value |
|---|---|
| Source | `git archive` of `5e835290166d5c3fd870eaba221daf81d85b49c0`, built in `build-5e83529\src` with a fresh venv |
| Python | CPython 3.13.14 (Microsoft Store build, x64) |
| Dependencies | `tools/windows-build-constraints.txt`: PyInstaller 6.22.2, pyinstaller-hooks-contrib 2026.6, PySide6 6.11.2, pygame-ce 2.5.8, PyYAML 6.0.3, setuptools 84.0.0, pip 26.2.1, wheel 0.48.0 (also applied to the isolated build backend) |
| Spectator | `0.1.0-alpha.1` @ `14089a7`, Godot 4.7.2 official template, `8a3bd1a4…d602` |
| Installer compiler | Inno Setup 6.7.3 |
| Build host | Windows 11 Pro 10.0.26120 (x64) |
| Logs | `evidence\build-5e83529-build_win.log`, `evidence\build-5e83529-iscc.log` |
| Reproducibility | PyInstaller output, the Inno archive and Godot exports are not byte-reproducible (timestamps, generated IDs). The shipped bytes are identified by the hashes recorded here and in `bytefray-files.txt`. Rebuilding the commit with the same pins reproduces the content, not the hashes |

**Artifact inventory.**

| Artifact | Location | Size | SHA-256 |
|---|---|---|---|
| Installer | `artifacts\Bytefray-5.1.0-alpha.1-Windows-x64-Setup.exe` | 113,834,819 | `4f964117103c114cdd1b9ac291ead76ca35fa4b9d8bd0c2903bcf0651bfac2f9` |
| Bundled Spectator | `{app}\bin\bytefray-spectator\bytefray-spectator.exe` | 137,850,648 | `8a3bd1a48430a0edd1faf8ca5c5b287ed1ecd06975c4e683f273562d428fd602` |
| Installed-file manifest | `{app}\bin\bytefray-files.txt`: 705 entries, each `<sha256>  <path>`; the deepest path is 107 characters (copy: `artifacts\bytefray-files.txt`) | 90,647 | `9a5c0b4e878d07c55b6a62488f8134f88a5467c4eabee6144d2780dab4691181` |
| Spectator build identity | `artifacts\SPECTATOR_BUILD.json` (installed as `{app}\bin\bytefray-spectator\SPECTATOR_BUILD.json`) | 1,633 | `6b5caf3ba2302d4fc9e22861aef38760cd5ce8688537ec31bd9a6568328a3740` |
| Checksums | `artifacts\SHA256SUMS` (the three files above; verified with `sha256sum -c`) | 283 | |

`Get-AuthenticodeSignature` reports **NotSigned** for the installer and the executables. No code signing, SmartScreen reputation or Microsoft submission was performed. The release notes tell users to compare the published `SHA256SUMS`.

**Conditions for publication** (project-lead decisions; none is satisfied by this report):

1. **LGPL corresponding source.** `licenses\THIRD_PARTY_NOTICES.md` maps every LGPL library to its exact source archive (Qt 6.11.2 modules, PySide6/Shiboken6 6.11.2, pygame-ce 2.5.8 with its SDL builds). Before publication, either host those archives with the release or ship a written offer. This choice was left to the project lead from review round 1 onward.
2. **Checksums.** Publish `SHA256SUMS` for the exact reviewed binary, SHA-256 `4f964117…c2f9`, with the release.
3. **Qualification environment.**
   - Qualified on one Windows 11 Pro 10.0.26120 x64 machine, under the developer's own non-elevated account. No clean machine, VM or second account was available, so this is **not clean-machine qualification**.
   - Bytefray 5.0 is not registered on this machine, so coexistence with a *registered* 5.0 was verified from source and with simulated 5.0 folders, not with a real 5.0 installation.
   - A link Windows lets Setup follow (one created by an administrator) could not be created without elevation. That branch, including the uninstaller's handling of a redirected root, is verified from source only.
4. **Unsigned distribution**, as above.
5. **Next installer.** Before an installer performs real cross-version cleanup (the first upgrade of alpha.1):
   - persist pending cleanup until eligible removals complete, and qualify interruption and deletion failure (R4-3);
   - keep the version registration, and raise the numeric file version with every public build.

   Earlier unpublished candidates are not supported predecessors.
6. **Repository publication.** Before any later publication of the Spectator repository, review commit author metadata against GitHub's no-reply policy:
   - Spectator commits use `personal-email identity (redacted)`;
   - commits on this release branch use `personal-email identity (redacted)` and `personal-email identity (redacted)`.

**Known limitations** (in the release notes and the compatibility record):

- Not code-signed; SmartScreen may warn.
- AMD64 only; per user only.
- The installation folder's path must stay under about 150 characters.
- Installation and data folders must not be reached through links Setup cannot follow, and the installation's `bin`, `docs` and `licenses` must not contain links.
- Installing an older 5.1 Alpha build over a newer one is refused.
- A refused installation shows a generic "Unhandled exception in script" dialog in the windowed applications.
- In Spectator 0.1.0-alpha.1, Tab and Space act on focused controls rather than switching perspective or playing.
- Agent Designer's entrant C selector has no accessible name.
- Spectator stores its settings in `%APPDATA%\Godot\app_userdata\Bytefray Spectator`, which uninstalling leaves in place.
- The first Spectator preparation of a long match is slow.
- The sensing demonstration generators are available from source only.
- Linux is qualified separately.
- E9 remains LOCKED; Requirement C remains NOT ESTABLISHED; M2-6 human evaluation is deferred to 5.2. Nothing here changes them.

**Workspace.**

- **Release branch.** `release/5.1.0-alpha.1-windows-candidate` is local only, with no upstream. Nothing was pushed, merged or tagged; no GitHub release was created or changed; nothing was uploaded.
- **Release worktree.** Clean after the report commit.
- **Protected checkouts.** These ten were snapshotted before and after:
  - main (`v6-research`) and `work/v6-m2-clean`;
  - the worktrees `p2-remediation-03-launcher`, `p1-remediation-02-wheel`, `p1-remediation-01-spectator-replace`, `m2-5-identity-integration`, `component-identity` and `spectator-integration`;
  - `Bytefray-Spectator-integration-20261017\spectator` and `Bytefray-Spectator`.

  Their HEAD, branch and working-tree status are unchanged (`evidence\protected-before.txt`, `evidence\protected-after.txt`). The hash of the shared non-Codex refs differs only because of this release branch. Recomputed with the branch at its creation point `0a962a3`, it equals the before value exactly (`evidence\protected-diff-explained.txt`).
  - The Codex ref count, the Spectator refs, the user's real per-user Bytefray data, `C:\Program Files\Bytefray` and `C:\ProgramData\Bytefray` are unchanged, and no `BYTEFRAY_ROOT` was written.
- **Spectator source repository.** Untouched; it was read and built from a separate clean clone.
- **Default folders.** `%LOCALAPPDATA%\Programs\Bytefray 5.1 Alpha`, `%LOCALAPPDATA%\Bytefray 5.1 Alpha`, the HKCU uninstall entry and the Start Menu group did not exist before this work. All are absent again. Each qualification data folder was archived under `install-tests\` before removal.
- **Disposable leftovers:**
  - the helper worktrees `5_1_alpha1_full-6aa5bed` (detached at `7b94790`) and `5_1_alpha1_gui-b95be54`;
  - the guard roots `%LOCALAPPDATA%\Temp\bfg-*` (no installation is registered from them);
  - the clean source exports `build-<sha>\`;
  - the push-disabled review clone.

**Recommendation.** Every installed check passes on the exact installer built from `5e83529`, and the independent review's final verdict is PASS WITH CONDITIONS. Publication still depends on decisions only the project lead can make: how to deliver LGPL corresponding source, and whether to accept unsigned distribution and a qualification limited to one developer machine without a clean-machine run.

**READY WITH CONDITIONS — PROJECT LEAD DECISION REQUIRED**
