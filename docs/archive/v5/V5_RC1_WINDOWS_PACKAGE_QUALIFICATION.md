# Bytefray V5 — RC1 Windows Package Qualification Report

**Date:** 2026-09-14
**Target Identity:** Bytefray 5.0.0-rc1 (`5.0.0rc1`)
**Branch:** `v5-research`
**Qualified HEAD SHA:** `bfd3bb82ac665e63f1e2d0990d6d2f17557941a1`
**Predecessor Rejected Candidate:** `84032674facc9c8720533f65afce00a3369cf7d6` (rejected in pre-RC remediation)
**Governing Gate:** Windows Release-Package Qualification Gate
**Final Verdict:** **WINDOWS RC1 PACKAGE QUALIFICATION PASSED**

---

## Executive Summary

The Windows release-package qualification gate for Bytefray 5.0.0-rc1 was executed from the clean, qualified successor candidate commit `bfd3bb82ac665e63f1e2d0990d6d2f17557941a1` to determine whether an ordinary Windows user can take the actual RC1 installer produced from the qualified source candidate, install Bytefray on a clean/fresh user state, launch it, use its major workflows, and remove/reinstall it successfully without depending on the source checkout, development virtual environment, or pre-existing developer state.

### Qualification Outcome

The source candidate, PyInstaller builds, onedir application trees (`dist\windows\*`), staged runtime workflows, and the actual Inno Setup installer lifecycle have now passed. The elevated lifecycle completion used the immutable installer `dist\installer\Bytefray-Setup-5.0.0-rc1.exe` at exactly 101,244,626 bytes and SHA-256 `F40F8F4A07B36B12B227300655FC458470093550111E08E6DD9A2797FD312D96`; it was not rebuilt.

Specifically:
1. **Historical Unelevated Gate Preserved (`FIND-WIN-03`):** The earlier silent attempt exited 1 before installation because the installer intentionally declares `PrivilegesRequired=admin`. That attempt created no files, shortcuts, uninstaller, or machine registry value. It remains recorded as an environment gate, not a runtime defect.
2. **Elevated Installer Execution:** UAC-elevated installer and uninstaller child processes completed successfully. After removing a previously registered historical Bytefray installation, the exact RC1 artifact performed a clean installation to `C:\Program Files\Bytefray`, set machine `BYTEFRAY_ROOT=C:\ProgramData\Bytefray`, created the two intended Start Menu shortcuts, registered the uninstaller, and installed all four executable trees and resources.
3. **Real Installed-Product Smoke:** From a fresh temporary working/data root outside the repository, with `PYTHONPATH` empty and no active development virtual environment, the installed copy reported `5.0.0rc1`, discovered all 21 starter agents, completed a representative battle and a three-match tournament, launched the Agent Designer and Pygame Replay Viewer, and passed bundled-pMARS checks.
4. **Uninstall and Reinstall:** The installed uninstaller exited 0 and removed program files, shortcuts, registration, and the machine environment value while retaining intended user data. The same installer was rehashed, reinstalled without rebuilding, and passed version, 21-agent discovery, and representative-battle checks from a second fresh root.
5. **Defect Classification & Verdict:** `FIND-WIN-03` is reclassified as **RESOLVED QUALIFICATION ENVIRONMENT GATE**. The exact installer has satisfied the Windows RC1 package gate.

The final verdict is **WINDOWS RC1 PACKAGE QUALIFICATION PASSED**.

---

## 1. Exact Source Candidate SHA & Phase 0 Baseline

A comprehensive Git audit was performed prior to any build actions to ensure the candidate baseline is sound and distinct from rejected predecessor commit `84032674facc9c8720533f65afce00a3369cf7d6`:

| Attribute | Audited Specification / Value | Status |
|---|---|:---:|
| **Repository Root** | `d:\Projects\BATTLE2` | PASS |
| **Branch** | `v5-research` | PASS |
| **HEAD SHA** | `bfd3bb82ac665e63f1e2d0990d6d2f17557941a1` | PASS |
| **Commit Subject** | `fix(v5): complete RC1 blocker remediation and source requalification` | PASS |
| **Predecessor Candidate** | `84032674facc9c8720533f65afce00a3369cf7d6` (rejected; remediated) | PASS |
| **Upstream Branch** | `origin/v5-research` | PASS |
| **Ahead/Behind** | Ahead by 3 commits (`d9a3dc2`, `8403267`, `bfd3bb8`), Behind 0 | PASS |
| **Worktree State** | Clean (`nothing to commit, working tree clean` prior to qualification doc update) | PASS |
| **Git Lock Files** | None (`.git/index.lock` absent) | PASS |
| **Active Build/Test Processes** | None | PASS |

---

## 2. Release Identity Verification (Phase 1)

All active release surfaces were verified for exact version agreement:

| Surface | File / Interface | Declared Identity | Status |
|---|---|---|:---:|
| **Project Configuration** | `pyproject.toml` (`[project].version`) | `5.0.0-rc1` | PASS |
| **Package Metadata** | `importlib.metadata.version('bytefray')` | `5.0.0rc1` | PASS |
| **Inno Setup Version** | `tools/installer.iss` (`AppVersion`) | `5.0.0rc1` | PASS |
| **Inno Setup Release Tag** | `tools/installer.iss` (`ReleaseTag`) | `5.0.0-rc1` | PASS |
| **CLI Version Output** | `bytefray.exe --version` | `Bytefray 5.0.0rc1, Agent API v2, result schema v2, replay schema v4, Python 3.13.14` | PASS |
| **GUI About Dialog** | `app/agent_designer.py` (`_on_about`) | `get_project_info()` -> `Bytefray 5.0.0rc1` | PASS |

---

## 3. Windows Build Environment Audit (Phase 2)

| Component | Audited Specification / Version |
|---|---|
| **Operating System** | Microsoft Windows 11 Pro 64-bit (`Microsoft Windows NT 10.0.26120.0`) |
| **OS Build Number** | `26120` |
| **Architecture** | `AMD64` (64-bit OS: `True`, 64-bit Process: `True`) |
| **Python Version** | Python 3.13.14 (64-bit) (`D:\Projects\BATTLE2\.venv\Scripts\python.exe`) |
| **Virtual Environment** | `D:\Projects\BATTLE2\.venv` |
| **PyInstaller** | `6.22.2` (hooks-contrib `2026.6`) |
| **Inno Setup Compiler** | Inno Setup 6 Command-Line Compiler 6.7.3 (`C:\Users\rasat\AppData\Local\Programs\Inno Setup 6\ISCC.exe`) |
| **PowerShell Core** | `7.6.6` (`pwsh.exe`) |
| **Windows PowerShell** | `5.1.26100.6972` (`powershell.exe`) |
| **Git Version** | `git version 2.51.0.windows.2` |
| **Key Package Dependencies** | `PySide6 6.11.2`, `pygame-ce 2.5.8`, `PyYAML 6.0.3`, `setuptools 84.0.0`, `wheel 0.48.0` |

---

## 4. Fresh Artifact Build & Provenance (Phases 3 & 4)

Fresh Windows release artifacts were produced directly from source candidate `bfd3bb82ac665e63f1e2d0990d6d2f17557941a1`.

### A. Build Execution
1. Executed `tools/build_win.ps1` via PowerShell. Built all 4 application targets cleanly. Internal smoke verified zero bytecode cache files (`.pyc`/`__pycache__`), verified dynamic import of Designer from unified dispatcher, verified standalone Designer startup, and verified `agents create` on all 4 scaffold templates in isolated temp data roots.
2. Executed Inno Setup 6 compilation: `& 'C:\Users\rasat\AppData\Local\Programs\Inno Setup 6\ISCC.exe' tools\installer.iss`.

### B. Distribution Artifact Provenance Table

| Artifact Name | Relative Path | Exact Size (Bytes) | SHA-256 Checksum | Build Timestamp |
|---|---|---:|---|---|
| **Windows Installer** | `dist\installer\Bytefray-Setup-5.0.0-rc1.exe` | 101,244,626 | `F40F8F4A07B36B12B227300655FC458470093550111E08E6DD9A2797FD312D96` | 2026-09-14 13:19:04 |
| **Unified Executable** | `dist\windows\bytefray\bytefray.exe` | 4,272,318 | `5B7876483F1090343C80CBA09739BE70204A49CA9134E8BDC21CB4CDC0B8B763` | 2026-09-14 13:15:52 |
| **CLI Executable** | `dist\windows\bytefray-cli\bytefray-cli.exe` | 2,870,502 | `01DBEE35E651FB1C4AE1014B39740B19B675770A5954AE9D3F85BAD5DADCC44A` | 2026-09-14 13:16:01 |
| **Agent Designer** | `dist\windows\bytefray-agent-designer\bytefray-agent-designer.exe` | 4,265,959 | `650FC999DAFD330652FEF56B973D516FFA165C415A5D7445B747FD953BE1DE09` | 2026-09-14 13:16:33 |
| **Replay Viewer** | `dist\windows\bytefray-replay-viewer\bytefray-replay-viewer.exe` | 3,938,532 | `CDA6FE6FC57C42AC5E0000156D4E8F10E9676E61AB6ACDB1C75F21B2B05AF445` | 2026-09-14 13:16:44 |

---

## 5. Isolated End-User Test Environment (Phase 5)

Testing was conducted completely decoupled from the developer checkout:
- **Application Staging Directory:** `C:\Users\rasat\Bytefray-Isolated-Test\Application`
  - `bin\bytefray\`, `bin\bytefray-cli\`, `bin\bytefray-agent-designer\`, `bin\bytefray-replay-viewer\`
  - `docs\README.md`, `docs\LICENSE`
- **Isolated User Data Root:** `C:\Users\rasat\Bytefray-Isolated-Test\Data`
  - `agents\`, `runs\_loose\`, `runs\test_battle\`, `runs\test_tournament\`, `cache\`
- **Working Directory:** `C:\Users\rasat\Bytefray-Isolated-Test`
- **Environment Isolation:**
  - `PYTHONPATH`: Explicitly cleared (`""`)
  - `VIRTUAL_ENV`: Inactive / cleared
  - `BYTEFRAY_ROOT`: Pointed explicitly to isolated data roots (`C:\Users\rasat\Bytefray-Isolated-Test\Data`, `FreshRoot1`, `FreshRoot2`)
  - No `sys.path` injection from `D:\Projects\BATTLE2`.

---

## 6. Clean Installation and Lifecycle Audit (Phases 6, 15, 16)

### A. Historical Unelevated Attempt: PRESERVED ENVIRONMENT GATE (FIND-WIN-03)

- The first silent unattended attempt exited **1** before installation because `tools/installer.iss` declares `PrivilegesRequired=admin` for its `Program Files` and HKLM operations.
- That unelevated attempt created no application directory, `unins000.exe`, Start Menu shortcuts, or machine environment value.
- No installer rebuild or product remediation followed. The already-qualified packaged application evidence remained intact while lifecycle work awaited an elevation-capable execution path.

### B. Elevated Interactive and Clean Installation: PASS

- The current completion run first reconfirmed source HEAD `bfd3bb82ac665e63f1e2d0990d6d2f17557941a1` and installer identity: 101,244,626 bytes, SHA-256 `F40F8F4A07B36B12B227300655FC458470093550111E08E6DD9A2797FD312D96`.
- An operator accepted normal Windows UAC elevation for the interactive installer. Windows initially reused a historical registration at `D:\Projects\BATTLE2\build\phase-f-28a10b8-20260909\manual-installer\app`; RC1 upgraded that registered tree and reported `5.0.0rc1`. This was retained as upgrade evidence but deliberately not counted as the clean, checkout-independent install.
- The generated uninstaller removed the historical registered application with exit 0. Program files, Start Menu shortcuts, registration, and machine `BYTEFRAY_ROOT` were removed while `C:\ProgramData\Bytefray` remained.
- A qualification-command quoting error then passed an unquoted path containing spaces to Inno Setup, producing a temporary `C:\Program` installation. Its registered uninstaller removed it cleanly with exit 0. This was an automation invocation error, not Bytefray product evidence, and it was excluded from the pass decision.
- With no Bytefray registration remaining, the unchanged installer was UAC-elevated using its declared default paths and exited 0. The resulting clean install was:
  - Application: `C:\Program Files\Bytefray`
  - Shared data: `C:\ProgramData\Bytefray`
  - Version: `5.0.0rc1`
  - Uninstaller: `C:\Program Files\Bytefray\unins000.exe`
  - Start Menu: `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Bytefray`

### C. Installer Registration, Resources, and Installed Product: PASS

- HKLM uninstall registration recorded `Bytefray 5.0.0rc1`, publisher `Bytefray Project`, canonical install/uninstall paths, and the installed unified executable as the display icon.
- Machine `BYTEFRAY_ROOT` was exactly `C:\ProgramData\Bytefray`.
- The two intended Start Menu shortcuts existed and resolved to the installed Agent Designer and Replay Viewer executables under `C:\Program Files\Bytefray`; neither shortcuts nor registry/configuration contained `D:\Projects\BATTLE2`.
- The optional desktop-shortcut task remained unselected as designed; no Bytefray shortcut was created on the common desktop.
- All four installed executable SHA-256 digests exactly matched their qualified `dist\windows` counterparts. `README.md`, `LICENSE`, bundled `pmars.exe`, GPLv2 `COPYING`, branding icons, 21 production starter manifests, and four authoring-template manifests were present.
- Associated Windows icons were extractable from the installer, unified executable, Agent Designer, and Replay Viewer.
- Installed-product smoke ran from `C:\Users\rasat\AppData\Local\Temp\bytefray-rc1-installed-9c12f144c19e41db8f881696a97f9830\work`, outside the source checkout, with an empty `PYTHONPATH`, no active `VIRTUAL_ENV`, and a fresh `BYTEFRAY_ROOT`.
- The first post-install harness call against that override root stopped at its precondition check because a fresh override does not contain the directories Inno Setup creates at the machine data root. No product workflow had launched. The rerun first materialized agents through the installed `bytefray agents` command and created the installer-declared empty `runs\_loose` directory; the harness then passed.
- Observed results: `--version` exit 0; exactly 21 starter agents; installed help surfaces exit 0; representative battle exit 0; three tournament matches completed with 0 failed/rejected/corrupted; Agent Designer remained live for the startup hold; Pygame Replay Viewer initialized and remained live for the startup hold; bundled pMARS match succeeded; invalid explicit `PMARS_CMD` failed safely with the expected normalized diagnostic.

### D. Canonical Uninstall: PASS

- `C:\Program Files\Bytefray\unins000.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART` ran UAC-elevated and exited 0.
- After uninstall: the application directory, Start Menu group, HKLM uninstall registration, and machine `BYTEFRAY_ROOT` were absent; no installed Bytefray process remained.
- Intended user data was preserved: `C:\ProgramData\Bytefray` remained with 488 files and 381 directories. `agents\runner\agent.yaml` retained SHA-256 `7EEE8297B9C3E2C322A99FFE82521C7256749972279C55C8BA03C3219F1CDE54` exactly across uninstall.

### E. Exact-Artifact Reinstall: PASS

- Immediately before reinstall, the same installer again measured 101,244,626 bytes and SHA-256 `F40F8F4A07B36B12B227300655FC458470093550111E08E6DD9A2797FD312D96`.
- UAC-elevated reinstall exited 0 and restored `C:\Program Files\Bytefray`, version `5.0.0rc1`, machine `BYTEFRAY_ROOT=C:\ProgramData\Bytefray`, two Start Menu shortcuts, and `unins000.exe`.
- The installed unified executable remained byte-identical to the qualified frozen payload (`5B7876483F1090343C80CBA09739BE70204A49CA9134E8BDC21CB4CDC0B8B763`).
- From a second fresh external root (`C:\Users\rasat\AppData\Local\Temp\bytefray-rc1-reinstall-f59e4a32f3da412d88aaa8ee86d510d5`), with empty `PYTHONPATH` and no active venv, the reinstalled product reported `5.0.0rc1`, materialized exactly 21 starters, and completed a representative V5 battle. The run produced `replay.jsonl` (64,452 bytes), `result.json` (3,860 bytes), and `summary.json` (1,521 bytes).

### F. Final Installed State

The exact RC1 artifact remains installed at `C:\Program Files\Bytefray` after successful clean-install, uninstall, and reinstall qualification. No rebuild, tag, upload, publication, or Linux qualification was performed.

---

## 7. Installed CLI Qualification (Phase 7)

The detailed qualification below was first executed using staged `C:\Users\rasat\Bytefray-Isolated-Test\Application\bin\bytefray\bytefray.exe` completely outside the source checkout. Section 6 records the compact corroborating rerun against the real Inno Setup-installed copy at `C:\Program Files\Bytefray\bin\bytefray\bytefray.exe`.

### A. Version and Help Surfaces
- `bytefray --version` -> `Bytefray 5.0.0rc1, Agent API v2, result schema v2, replay schema v4, Python 3.13.14` (Exit: 0).
- `bytefray --help` -> Help display for subcommands `{run,tournament,replay,design,agents}` (Exit: 0).
- `bytefray-cli --help` -> Help display for CLI runner options (Exit: 0).
- Major subcommand help (`run`, `tournament`, `replay`, `agents`) all exit 0.

### B. Agent Discovery in Fresh Root
- Executed `bytefray agents` and `bytefray-cli --list-agents` against fresh data root.
- Verified all **21 production starter agents** materialized under `<data_root>\agents\`:
  - VM Starters (4): `runner`, `seeker`, `spiral`, `writer`
  - Agent API v1 Starters (7): `adaptive`, `claimer`, `hunter`, `raider`, `sentinel`, `strider`, `wanderer`
  - Agent API v2 Starters (10): `v4_claimer`, `v4_concentrated_attacker`, `v4_defender_scout`, `v4_local_defender`, `v4_quorum`, `v4_scout`, `v5_core_defender`, `v5_dual_team`, `v5_region_attacker`, `v5_scout_striker`
- Starter directory count confirmed: exactly 21.

### C. Normal Battle Execution
- Command: `bytefray run --a-type v5_core_defender --b-type v5_region_attacker --seed 42 --ticks 200 --replay <path>`
- Exit code: 0.
- Replay artifact: `replay.jsonl` produced (64,452 bytes), verified `schema: battle2.replay`, `schema_version: 4`.
- Result artifact: `result.json` produced (3,860 bytes), verified `schema: battle2.result`, `schema_version: 2`.
- Summary artifact: `summary.json` produced (1,521 bytes).
- Winner correctly identified as `v5_region_attacker` (score 60.0 vs 54.0).

### D. Invalid Compatibility Case Rejection
- Mismatched ruleset test: `bytefray run --a-type v5_core_defender --b-type v5_region_attacker --ruleset bytefray-rules-1`
  - Output: `ERROR: Ruleset 'bytefray-rules-1' does not support entrant metadata: A (python, Agent API 2), B (python, Agent API 2).`
  - Exit code: 2 (clean error rejection).
- Unknown ruleset test: `bytefray run ... --ruleset invalid-ruleset` -> Exit code: 2.

### E. Tournament Execution
- Command: `bytefray tournament --rounds 1 --ticks 100 --seed 42 --output <dir> v5_core_defender v5_region_attacker v5_scout_striker`
- Result: 3 matches completed, 0 failed, 0 rejected, 0 corrupted.
- State file: `tournament.json` produced (2,107 bytes) recording standings.
- Match subdirectories: Each match folder contains canonical `replay.jsonl` and `result.json`.

---

## 8. Installed GUI, Designer, and Replay Viewer Qualification (Phase 8 & 9)

1. **Unified Dispatcher Launch:** `bytefray.exe design` launched with `BYTEFRAY_GUI_SMOKE_EXIT_MS=1500`, cleanly initialized Qt event loop, and exited with code 0 without traceback.
2. **Standalone Designer Launch:** `bytefray-agent-designer.exe` launched with `BYTEFRAY_GUI_SMOKE_EXIT_MS=1500`, cleanly initialized, and exited with code 0.
3. **Headless Replay Playback:** `bytefray-replay-viewer.exe --replay <path> --renderer headless` played all 55 match ticks and reported winner B (Exit: 0).
4. **PyGame CE Replay Viewer Launch:** `bytefray-replay-viewer.exe --replay <path> --renderer pygame --tick-delay 0.05` initialized graphical SDL display successfully and ran until stopped cleanly.
5. **Agent Scaffold & Packaging Workflows:**
   - `bytefray agents create test_qual_agent --api-version 2` (Exit: 0).
   - `bytefray agents validate test_qual_agent` -> Validated API v2 dry-run action (`WRITE operand=0 value=165`) (Exit: 0).
   - `bytefray agents test test_qual_agent` -> Ran development match against reference agent, produced `result.json`, `replay.jsonl`, `summary.json`, `trace.jsonl` (Exit: 0).
   - `bytefray agents export test_qual_agent --output <pkg>` -> Exported portable `.bytefray-agent` archive (2,117 bytes, SHA-256 `cd03754e8876ee0ad31dd845d78d1c29d4e717cd373653c91927f3ab93cefaf6`) (Exit: 0).
   - `bytefray agents package show <pkg>` -> Verified integrity and structure without execution (Exit: 0).
   - `bytefray agents evaluate test_qual_agent --opponents v5_region_attacker --ticks 50` -> Successfully ran complete 16-match candidate/baseline evaluation matrix, producing `evaluation.json` (Exit: 0).

---

## 9. Tournament Missing-Result Resume Integrity Probe (Phase 11)

Targeted probe against the previously blocking Tournament resume integrity defect:
1. **Baseline State:** Completed small 3-match tournament in isolated data root. Match 0 (`scheduled_7bbaea2d1c1e355746de26a9`, `match_81048c917d4d8e5a01cc043f`, `result_f8b8209730665ecc9fb0bf32`) recorded `status: completed`.
2. **Adversarial Damage:** Deleted canonical `matches\000001-r1-v5_core_defender-vs-v5_region_attacker\result.json`.
3. **Resume Without Authorization:** Ran `bytefray tournament --rounds 1 --ticks 100 --seed 42 --output <dir> ...` without `--retry-failed`.
   - **Observed Behavior:**
     - Tournament detected missing result.
     - Did **not** silently re-run.
     - Match 0 marked `status: corrupted`, `error_code: resumed_result_mismatch`, `error_message: result.json is not present`.
     - Tournament exited with non-zero exit code **1**.
4. **Authorized Retry:** Ran `bytefray tournament ... --retry-failed ...`.
   - **Observed Behavior:**
     - Retry authorized.
     - Match 0 re-executed cleanly.
     - `result.json` recreated (4,030 bytes).
     - Match 0 restored to `status: completed`.
     - Tournament exited with code **0**.

---

## 10. Replay History Click-Time Association Integrity Probe (Phase 10)

Targeted probe against the previously blocking Replay History stale-association defect:
1. **Discovery & Indexing:** `ReplayHistoryService.open(data_root)` indexed runs into disposable cache `cache/replay_history/index-v1.sqlite3`.
2. **Initial Verification:** Resolved `test_battle` occurrence (`match_1c3791c3ac11532d137d3e15`, `result_5d5b5c940cde441566f01ac8`). `verify_replay_integrity(resolution)` reported:
   - `status: ReplayIntegrityStatus.VERIFIED`
   - `failure: None`
3. **Adversarial Mutation:** Modified authoritative `result.json`'s `result_id` to `result_stale_association_spoofed`. Replay bytes on disk remained completely untouched.
4. **Re-verification with Cached Resolution:** Invoked `verify_replay_integrity(resolution)` representing a click-time launch on the existing table row.
   - **Observed Behavior:**
     - Status: `ReplayIntegrityStatus.MISMATCH`
     - Failure Code: `ReplayPreflightFailure.RESULT_ASSOCIATION_MISMATCH`
     - Blocks Launch: `True`
     - Diagnostic: `The selected result_id no longer matches its parent record.`
   - Cached stale association was strictly rejected.
5. **Restoration:** Restored original `result.json` bytes. `verify_replay_integrity(resolution)` immediately returned `VERIFIED`.

---

## 11. Fresh-Root Multi-Shell Validation (Phase 12)

Tested in independently fresh data roots under both supported shells:

| Environment / Shell | Command | Starter Count | Tiny Match Result | Replay Produced | Status |
|---|---|:---:|---|:---:|:---:|
| **PowerShell Core 7.6.6** | `bytefray agents` / `bytefray run --a-type runner --b-type writer` | 21 | Exit 0 | 42,615 B | PASS |
| **Windows PowerShell 5.1.26100** | `bytefray agents` / `bytefray run --a-type seeker --b-type spiral` | 21 | Exit 0 | 38,049 B | PASS |

---

## 12. Installed File & Resource Audit (Phase 13)

Audited against `tools/check_wheel.py` release resource contract from the staged payload, then corroborated in the real installed tree as recorded in Section 6:

| Resource Category | Required Item | Observed Path / Presence | Status |
|---|---|---|:---:|
| **Executables** | `bytefray.exe` | `bin\bytefray\bytefray.exe` (4,272,318 bytes) | PASS |
| **Executables** | `bytefray-cli.exe` | `bin\bytefray-cli\bytefray-cli.exe` (2,870,502 bytes) | PASS |
| **Executables** | `bytefray-agent-designer.exe` | `bin\bytefray-agent-designer\bytefray-agent-designer.exe` (4,265,959 bytes) | PASS |
| **Executables** | `bytefray-replay-viewer.exe` | `bin\bytefray-replay-viewer\bytefray-replay-viewer.exe` (3,938,532 bytes) | PASS |
| **pMARS Binaries** | `pmars.exe` (windows) | `_internal\pmars\windows\pmars.exe` (150,528 bytes) | PASS |
| **pMARS License** | `COPYING` (GPLv2) | `_internal\pmars\windows\COPYING` (17,997 bytes) | PASS |
| **Branding Icons** | `bytefray-icon.png` | Present in `bytefray`, `designer`, `viewer` `_internal` | PASS |
| **Starter Agents** | 21 starters (manifests + code) | All 21 starter directories present in `_internal` | PASS |
| **Templates (API v1)** | `agent_template` (basic + annotated) | All 4 files present in `_internal` | PASS |
| **Templates (API v2)** | `agent_template_v2` (basic + annotated) | All 4 files present in `_internal` | PASS |
| **Documentation** | `README.md`, `LICENSE` | Present under `docs\` | PASS |

---

## 13. Candidate & Source-Tree Integrity Post-Qualification (Phases 17 & 18)

Final audit of candidate repository and generated assets:

| Check | Expected | Observed | Status |
|---|---|---|:---:|
| **Candidate Commit** | `bfd3bb82ac665e63f1e2d0990d6d2f17557941a1` | `bfd3bb82ac665e63f1e2d0990d6d2f17557941a1` | PASS |
| **Tracked Source Tree** | Clean except qualification documentation update | Only `docs/research/v5/V5_RC1_WINDOWS_PACKAGE_QUALIFICATION.md` modified | PASS |
| **Installer Hash** | Stable SHA-256 | `F40F8F4A07B36B12B227300655FC458470093550111E08E6DD9A2797FD312D96` | PASS |
| **Release Artifact** | `Bytefray-Setup-5.0.0-rc1.exe` | Generated in `dist\installer\` (101,244,626 bytes) | PASS |

---

## 14. Findings and Defect Classification

| Finding ID | Description | Severity | Disposition |
|---|---|---|---|
| **FIND-WIN-01** | Stale candidate commit `84032674` previously at HEAD. | Former Blocker | **RESOLVED:** Successor commit `bfd3bb82ac665e63f1e2d0990d6d2f17557941a1` committed and qualified. |
| **FIND-WIN-02** | System machine/user registry variable `BYTEFRAY_ROOT` was set on dev host to historical test path (`D:\Projects\BATTLE2\build\phase-f-28a10b8-20260909\...`). | NON-BLOCKING (Host Environment) | Resolved by explicit environment isolation during test execution. Does not affect clean end-user systems. |
| **FIND-WIN-03** | The first silent installer attempt exited 1 under an unelevated process because the installer intentionally declares `PrivilegesRequired=admin`. | **RESOLVED QUALIFICATION ENVIRONMENT GATE** | UAC-elevated clean install, real installed-product smoke, uninstaller cleanup, and exact-artifact reinstall all passed. This was not a Bytefray product defect. |

---

## 15. Qualification Boundary Distinctions & Final Verdict

### Qualification Boundary Distinctions

For absolute procedural clarity:

1. **Windows RC1 Package Qualification:** **PASSED** for exact installer SHA-256 `F40F8F4A07B36B12B227300655FC458470093550111E08E6DD9A2797FD312D96` at source SHA `bfd3bb82ac665e63f1e2d0990d6d2f17557941a1`. `FIND-WIN-03` is resolved as a qualification-environment gate.
2. **Linux RC1 Package Qualification:** **NOT STARTED** (independent qualification gate; requires qualified source candidate and clean Linux wheel/sdist environment).
3. **RC1 Publication Authorization:** **NOT AUTHORIZED**. Under no circumstances may Bytefray 5.0.0-rc1 be tagged, released, or published until both Windows and Linux package qualification gates pass completely.

---

### Final Verdict

# `WINDOWS RC1 PACKAGE QUALIFICATION PASSED`
