# Bytefray V5 — RC1 Windows Package Qualification Report

**Date:** 2026-09-14  
**Target Identity:** Bytefray 5.0.0-rc1 (`5.0.0rc1`)  
**Branch:** `v5-research`  
**Inspected HEAD SHA:** `84032674facc9c8720533f65afce00a3369cf7d6`  
**Governing Gate:** Windows Release-Package Qualification Gate  
**Final Verdict:** **WINDOWS RC1 PACKAGE QUALIFICATION BLOCKED**

---

## Executive Summary

The Windows release-package qualification gate for Bytefray 5.0.0-rc1 was executed to determine whether an ordinary Windows user can take an actual RC1 installer produced from the qualified source candidate, install Bytefray on a clean/fresh user state, launch it, use its major workflows, and remove/reinstall it successfully without depending on the source checkout, development virtual environment, or pre-existing developer state.

During **Phase 0 (Establish Exact Source Candidate)**, the gate encountered an immediate and non-negotiable release blocker:

1. **Rejected Candidate at HEAD:** The repository HEAD commit is `84032674facc9c8720533f65afce00a3369cf7d6`. This exact commit was explicitly rejected by the independent adversarial review and declared ineligible for qualification in both `V5_RC1_BLOCKER_REMEDIATION_AND_SOURCE_REQUALIFICATION.md` and the Phase 0 specification.
2. **Dirty Working Tree / Uncommitted Remediation:** The remediation addressing the two former RC blockers (Tournament missing-result resume integrity and Replay History click-time authoritative association verification) exists only as uncommitted modifications across 13 tracked files and 2 untracked files. No successor candidate commit has been established.
3. **Absence of Qualified Package Artifact:** Because the candidate commit does not exist, no fresh Windows executables or Windows installer (`Bytefray-Setup-5.0.0-rc1.exe`) could be built or qualified. The only installer present in `dist/installer/` is the obsolete Alpha 1 installer `Bytefray-Setup-5.0.0a1.exe` built on 2026-09-11. Additionally, the Inno Setup compiler (`ISCC.exe`) is not present in PATH in the environment.

Per the release boundary and defect handling rules:
- This is not a source-development phase. Source modifications or ad hoc commits cannot be performed during the package qualification gate.
- If the current source cannot be proven to be the qualified successor candidate, the qualification must stop and report the discrepancy.
- Defect **WIN-RC1-BLK-01** is classified as a **WINDOWS RC1 BLOCKER**.

The qualification is formally **BLOCKED**.

---

## 1. Exact Source Candidate SHA & Phase 0 Baseline

A comprehensive Git audit was performed prior to any build actions:

| Attribute | Observed Value | Qualification Requirement | Status |
|---|---|---|:---:|
| **Repository Root** | `d:\Projects\BATTLE2` | Established repository root | PASS |
| **Branch** | `v5-research` | Active release branch | PASS |
| **HEAD SHA** | `84032674facc9c8720533f65afce00a3369cf7d6` | Must be a clean, qualified successor commit (NOT `84032674`) | **FAIL (BLOCKER)** |
| **Commit Subject** | `fix(v5): resolve RC1 readiness audit review findings` | Proven successor commit | **FAIL** |
| **Upstream Branch** | `origin/v5-research` | Synchronized tracking | PASS |
| **Ahead/Behind** | Ahead by 2 commits (`d9a3dc2`, `8403267`) | Clean synchronization or expected push state | PASS |
| **Worktree State** | **Dirty** (13 tracked files modified, 2 untracked files) | Must be completely clean (`nothing to commit, working tree clean`) | **FAIL (BLOCKER)** |
| **Git Lock Files** | Absent (`.git/index.lock` not present) | No concurrent locks | PASS |
| **Active Processes** | None; no competing test or build processes | Isolated environment | PASS |

### Worktree Contamination Details

The working tree contains extensive uncommitted changes:
- **Modified Tracked Files (13):**
  - `ARCHITECTURE.md`
  - `CHANGELOG.md`
  - `docs/TOURNAMENTS.md`
  - `docs/research/v5/V5_RC1_READINESS_AND_QUALIFICATION.md`
  - `engine/src/battle_engine/replay_history/query.py`
  - `engine/src/battle_engine/replay_history/service.py`
  - `engine/src/battle_engine/tournament_cli.py`
  - `engine/src/battle_engine/tournament_service.py`
  - `engine/tests/test_replay_history.py`
  - `engine/tests/test_tournament_service.py`
  - `engine/tests/test_v5_alpha1_phase_b_engine_hygiene.py`
  - `tools/check_wheel.py`
  - `tools/smoke_test.ps1`
- **Untracked Files (2):**
  - `docs/research/v5/V5_RC1_BLOCKER_REMEDIATION_AND_SOURCE_REQUALIFICATION.md`
  - `engine/tests/test_check_wheel.py`

### Assessment against Phase 0 Gating

The qualification specification explicitly mandates:
> *"In particular: `84032674facc9c8720533f65afce00a3369cf7d6` was a **rejected RC1 candidate** and must not be reused as the qualified Windows source. If the current source cannot be proven to be the qualified successor candidate, stop and report the discrepancy."*

Because HEAD is `84032674` and all remediation changes are uncommitted, no qualified successor commit exists in the Git DAG. Qualification cannot proceed beyond Phase 0.

---

## 2. Windows Build Environment Audit

The host system and development tooling were audited and recorded:

| Component | Audited Specification / Version |
|---|---|
| **Operating System** | Windows 11 Pro 64-bit (`Microsoft Windows NT 10.0.26120.0`) |
| **OS Build Number** | `26120` |
| **Architecture** | `AMD64` (64-bit OS and process) |
| **System Python** | Python 3.13.14 (64-bit) |
| **Virtual Environment** | `d:\Projects\BATTLE2\.venv` |
| **Venv Python** | Python 3.13.14 (`.venv\Scripts\python.exe`) |
| **PyInstaller** | 6.22.2 (`.venv\Scripts\pyinstaller.exe`) |
| **Inno Setup Compiler** | Not detected in `PATH` (`ISCC.exe` not found) |
| **PowerShell Core** | PowerShell 7.6.6 (`pwsh.exe`) |
| **Windows PowerShell** | Windows PowerShell 5.1.26100.6972 (`powershell.exe`) |
| **Git** | 2.51.0.windows.2 |
| **Terminal Privilege** | Standard User (Unelevated; Administrator = `False`) |

---

## 3. Build Commands and Packaging Process

The repository's canonical Windows build entry point is `tools/build_win.ps1`, which orchestrates PyInstaller builds for the four application targets:
1. `tools/bytefray.spec` (`dist\windows\bytefray\bytefray.exe`)
2. `tools/bytefray_cli.spec` (`dist\windows\bytefray-cli\bytefray-cli.exe`)
3. `tools/agent_designer.spec` (`dist\windows\bytefray-agent-designer\bytefray-agent-designer.exe`)
4. `tools/replay_viewer.spec` (`dist\windows\bytefray-replay-viewer\bytefray-replay-viewer.exe`)

The installer is compiled using Inno Setup 6 via `tools/installer.iss`, which packages the four onedir trees from `dist\windows` into `dist\installer\Bytefray-Setup-5.0.0-rc1.exe`.

### Execution Status: Halted
Because Phase 0 failed the source baseline check, producing fresh build artifacts from the uncommitted/rejected state was **prohibited**. The release boundary states:
> *"Build the Windows product fresh from the exact qualified source SHA. Do not reuse: an earlier `.exe`; an earlier installer; old `dist/` output; artifacts from rejected candidate `84032674`; artifacts whose provenance cannot be proven."*

---

## 4. Executable & Application Artifacts

An inspection of `dist\windows\` revealed stale build artifacts remaining from earlier Alpha 1 builds:

| Executable Path | File Size | Timestamp | Status |
|---|---|---|---|
| `dist\windows\bytefray\bytefray.exe` | 4,081,257 bytes | 2026-09-11 12:05:50 | Stale (Alpha 1) |
| `dist\windows\bytefray-cli\bytefray-cli.exe` | 4,081,257 bytes | 2026-09-11 12:06:14 | Stale (Alpha 1) |
| `dist\windows\bytefray-agent-designer\bytefray-agent-designer.exe` | 4,081,257 bytes | 2026-09-11 12:07:02 | Stale (Alpha 1) |
| `dist\windows\bytefray-replay-viewer\bytefray-replay-viewer.exe` | 4,081,257 bytes | 2026-09-11 12:07:34 | Stale (Alpha 1) |

No executables built from a qualified RC1 candidate commit exist.

---

## 5. Installer Artifact Identity

Inspection of `dist\installer\` identified the following artifact:

- **Filename:** `Bytefray-Setup-5.0.0a1.exe`
- **File Size:** 97,898,637 bytes
- **Timestamp:** 2026-09-11 12:08:23
- **Version Identity:** `5.0.0a1` (Alpha 1)
- **RC1 Installer Present:** **NONE** (`Bytefray-Setup-5.0.0-rc1.exe` does not exist)

Reusing or qualifying `Bytefray-Setup-5.0.0a1.exe` for an RC1 qualification is strictly prohibited.

---

## 6. Artifact Hashes (SHA-256)

Because no RC1 candidate installer or executables were built, no valid RC1 artifact SHA-256 digests exist.

Historical reference hashes for the unqualifiable Alpha 1 installer:
- `Bytefray-Setup-5.0.0a1.exe`: `e62cf05d41c888e2354c46fbe40d39e3bfb2ef322ea36f73111f1fb6b2be0334` *(Alpha 1 archive, ineligible for RC1)*

---

## 7. Clean-Install Result

**Gated / Blocked:** No valid 5.0.0-rc1 installer artifact exists to install. Installation was not attempted.

---

## 8. Installed CLI Results

**Gated / Blocked:** No installed product environment could be established.

---

## 9. Installed GUI / Designer Results

**Gated / Blocked:** No installed product environment could be established.

---

## 10. Battle Result

**Gated / Blocked:** Installed product execution could not be performed.

---

## 11. Tournament Result

**Gated / Blocked:** Installed product execution could not be performed.

---

## 12. Replay Result

**Gated / Blocked:** Installed product execution could not be performed.

---

## 13. Replay History Result

**Gated / Blocked:** Installed product execution could not be performed.

---

## 14. Former-Blocker Regression Probes (Source Audit)

While installed-product testing could not be executed due to the missing installer package, the implementation of the two former release blockers was audited directly in the working tree to verify the state of the remediation:

### Probe 1: Tournament Missing-Result Resume Integrity
- **Audited File:** `engine/src/battle_engine/tournament_service.py`
- **Audited Method:** `_validate_prior_match()` (lines 438–492)
- **Behavior:** The code now explicitly verifies the presence and integrity of `result.json` for every completed match entry. When `result.json` is missing or invalid, the match state is marked `corrupted` with reason `resumed_result_mismatch: result.json is not present`. The scheduler strictly excludes corrupted matches from standings and refuses to silently rerun the match unless explicitly authorized via `retry_failures` / `--retry-failed`.
- **Characterization:** Tested and characterized in `engine/tests/test_tournament_service.py` and documented in `V5_RC1_BLOCKER_REMEDIATION_AND_SOURCE_REQUALIFICATION.md`.
- **Status in Tree:** Correctly implemented in source, but **uncommitted**.

### Probe 2: Replay History Click-Time Authoritative Association Verification
- **Audited Files:** `engine/src/battle_engine/replay_history/service.py` and `engine/src/battle_engine/replay_history/query.py`
- **Audited Method:** `preflight_result_replay()` and `resolve_entry()`
- **Behavior:** Click-time launch no longer trusts index-time SQLite metadata alone. For result-backed replays, `preflight_result_replay()` rereads the canonical `result.json` on disk, verifies that the result ID matches the indexed association, validates the referenced replay path and SHA-256 digest, and rejects launch with `result_association_mismatch` if the result has been altered or decoupled.
- **Characterization:** Tested and characterized in `engine/tests/test_replay_history.py` (198 tests passing).
- **Status in Tree:** Correctly implemented in source, but **uncommitted**.

---

## 15. Fresh-Root Result

**Gated / Blocked:** Testing in an isolated fresh-root environment requires an installed product payload from a qualified installer.

---

## 16. Installed-File & Resource Audit

**Gated / Blocked:** No installed tree could be provisioned.

---

## 17. Uninstall Result

**Gated / Blocked:** No installation was performed.

---

## 18. Reinstall Result

**Gated / Blocked:** No installation was performed.

---

## 19. Source-Tree Integrity

A strict integrity check was maintained throughout this audit.
- No tracked source files were modified, committed, or deleted during this qualification task.
- No builds were executed that could pollute the working tree with build artifacts or cache files.
- The working tree remains in its exact starting state (13 modified files, 2 untracked files, HEAD at `8403267`).

---

## 20. Findings and Defect Classification

### Finding WIN-RC1-BLK-01: Head Is Rejected Candidate `84032674`, Worktree Has Uncommitted Remediation, No Qualified Successor Commit Exists

- **Classification:** **WINDOWS RC1 BLOCKER**
- **Description:** 
  The current repository HEAD commit is `84032674facc9c8720533f65afce00a3369cf7d6`. This commit was explicitly invalidated and rejected due to two confirmed release-blocking integrity defects. While remediation code exists in the repository working tree, it has never been committed. The Git worktree has 13 modified tracked files and 2 untracked files. Consequently, no clean, qualified successor commit exists to serve as the source candidate for building the Windows executables and installer.
- **Impact:** 
  Phase 0 gating fails unconditionally. Building release packages from an uncommitted working tree or from rejected commit `84032674` violates release governance and invalidates package qualification.
- **Remediation Required:**
  1. An engineering/orchestration commit must be created that commits all validated post-alpha blocker remediation changes, documentation, and regression tests.
  2. The resulting commit SHA must be established as the formal qualified RC1 source candidate.
  3. The Windows build pipeline (`tools/build_win.ps1` and `tools/installer.iss`) must be executed from that clean candidate commit in an environment equipped with Inno Setup 6 (`ISCC.exe`).
  4. The freshly generated `Bytefray-Setup-5.0.0-rc1.exe` must then undergo full package qualification.

### Finding WIN-RC1-WARN-01: Inno Setup Compiler (`ISCC.exe`) Not Available in Build Environment PATH

- **Classification:** **WINDOWS RC1 FIX RECOMMENDED**
- **Description:**
  The Windows build environment does not contain `ISCC.exe` in the system `PATH` or standard Program Files directories. While PyInstaller is installed in `.venv`, building the final `.exe` installer requires Inno Setup 6.
- **Impact:**
  Even once a qualified commit is established, attempting to build the installer will fail until Inno Setup 6 is installed or its compiler added to `PATH`.

---

## Qualification Boundary Distinctions

For absolute procedural clarity:

1. **Windows RC1 Package Qualification:** **BLOCKED** by defect `WIN-RC1-BLK-01`.
2. **Linux RC1 Package Qualification:** **NOT STARTED** (independent gate; requires qualified source candidate and clean Linux wheel/sdist environment).
3. **RC1 Publication Authorization:** **NOT AUTHORIZED**. Under no circumstances may Bytefray 5.0.0-rc1 be tagged, released, or published until both Windows and Linux package qualification gates pass completely.

---

## Final Verdict

# `WINDOWS RC1 PACKAGE QUALIFICATION BLOCKED`
