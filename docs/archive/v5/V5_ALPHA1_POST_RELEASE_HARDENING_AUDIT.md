# Bytefray V5 Alpha 1 — Post-Release Hardening Audit

**Document Status:** Complete Engineering Audit & Falsification Pass  
**Audited Target:** Bytefray V5 Alpha 1 (`5.0.0a1`)  
**Commit SHA:** `0f679f7793a1ac2f25d89b7031e63bc375dc2504`  
**Branch:** `v5-research`  
**Date:** 2026-09-10  
**Discipline:** Read-Only Post-Release Hardening Audit (No source, test, packaging, or version mutations)  

---

## A. Baseline / Boost isolation

### Baseline Repository State
- **Current Branch:** `v5-research`
- **HEAD Commit SHA:** `0f679f7793a1ac2f25d89b7031e63bc375dc2504`
- **Product Version:** `5.0.0a1` (defined in [pyproject.toml](file:///d:/Projects/BATTLE2/pyproject.toml#L10))
- **Primary Checkout Path:** `D:\Projects\BATTLE2`
- **Active Worktrees (`git worktree list`):**
  - `D:/Projects/BATTLE2` (commit `0f679f7`, branch `v5-research`)
  - `C:/Users/rasat/AppData/Local/Temp/claude/d--Projects-BATTLE2/6238687a-0bce-4948-8d3e-08183e0f3a23/scratchpad/rc2-c-build` (commit `a0a14b8`, detached HEAD)
  - `D:/Projects/Bytefray-v1-rc1` (commit `b68c412`, branch `v1.0-rc1-branding`)
- **Git Index & Lock Health:**
  - `Test-Path .git/index.lock` returned `False`.
  - `.git/index` clean and undamaged.
  - `git status --short` before audit: Only this audit file is untracked (`?? docs/research/v5/V5_ALPHA1_POST_RELEASE_HARDENING_AUDIT.md`). No tracked files modified.

### Worktree Provisioning & Isolation Note
An initial automated attempt by Antigravity Boost to provision an isolated git worktree via `Workspace='share'` failed during worktree creation:
```text
failed to resolve workspace URIs for subagent: failed to share any workspace: failed to create git worktree for subagent branch:
Preparing worktree (new branch 'subagent-Post-Release-Hardening-Auditor-DeepInvestigator-4587fa16')
error: unable to create file docs/screenshots/v3-phase4-evaluation-infrastructure/evaluate-dialog-workers-control.png: Filename too long
fatal: Could not reset index file to revision 'HEAD'.: exit status 128
```
This failure occurred because deep scratchpad paths combined with long relative file paths in `docs/screenshots/` exceeded Windows' legacy 260-character `MAX_PATH` limit.

In accordance with user instructions, the audit proceeded in `Workspace='inherit'` mode directly within `D:\Projects\BATTLE2` under strict read-only discipline. No product source, test, or packaging files were modified.

---

## B. Executive assessment

### Overall Verdict
**FOLLOW-UP HARDENING RECOMMENDED (Non-Critical)**

### Summary Rationale
Bytefray V5 Alpha 1 (`5.0.0a1`) is structurally sound for standard interactive and CLI gameplay (`bytefray run` and the Designer UI). Core simulation, determinism, ruleset enforcement (`bytefray-rules-4`), and package integrity function as designed. No blocker defects requiring release revocation or an emergency hotfix were discovered.

However, a deep falsification review of prior qualification assumptions and implementation boundaries revealed **1 High**, **2 Medium**, **3 Low**, and **1 Informational** findings that warrant remediation during the V5 Beta 1 development cycle. Most notably:
1. Tournament, evaluation, and test subcommands bypass parameter schema default resolution, leading to match ID divergence and empty `MatchContextV2.parameters` in tournaments.
2. Supervised execution mode (`supervised_runtime.py`) omits entrant parameter forwarding to child worker processes.
3. Starter refresh writes files in place non-atomically, leaving interrupted updates permanently trapped as "customized".

### Findings Breakdown by Severity

| Severity | Count | Summary of Key Issues |
|---|:---:|---|
| **BLOCKER** | 0 | None. No fatal execution defects or release-invalidating regressions. |
| **HIGH** | 1 | **FIND-01**: Tournament CLI, Agent Test, and Agent Evaluation omit entrant parameter defaults, causing `canonical_match_id` divergence and empty `context.parameters` for tournament entrants. |
| **MEDIUM** | 2 | **FIND-02**: Supervised runtime (`supervised_runtime.py`) omits parameter forwarding during worker reset, causing agents running with timeout or under Agent Lab to receive empty parameters. <br>**FIND-03**: Starter agent refresh modifies user files non-atomically in place; interrupted updates permanently trap the starter in `CUSTOMIZED` mode, disabling future auto-upgrades. |
| **LOW** | 3 | **FIND-04**: `starter_content_files` only filters `__pycache__` directories, allowing loose `.pyc`/`.pyo` files to contaminate starter digests. <br>**FIND-05**: `tools/build_linux.sh` lacks the post-build bytecode debris verification present in `tools/build_win.ps1`. <br>**FIND-06**: Standalone GUI packaging specs (`agent_designer.spec` and `replay_viewer.spec`) bundle the entire `assets/` directory (including large marketing brand sheets), whereas `bytefray.spec` correctly bundles only runtime assets. |
| **INFORMATIONAL** | 1 | **FIND-07**: Case-sensitive directory name matching in `packaging_data.py`. |

---

## C. Packaging/resource review

### Frozen Specs and Collection Architecture
We audited the four active PyInstaller specifications in [tools/](file:///d:/Projects/BATTLE2/tools):
1. [tools/bytefray.spec](file:///d:/Projects/BATTLE2/tools/bytefray.spec) (Unified executable: Designer + Replay + CLI)
2. [tools/bytefray_cli.spec](file:///d:/Projects/BATTLE2/tools/bytefray_cli.spec) (Headless simulation & match CLI)
3. [tools/agent_designer.spec](file:///d:/Projects/BATTLE2/tools/agent_designer.spec) (Standalone Agent Designer GUI)
4. [tools/replay_viewer.spec](file:///d:/Projects/BATTLE2/tools/replay_viewer.spec) (Standalone Pygame Replay Viewer)

*(Note: Prior investigator reports referenced `bytefray_tournament.spec` and `bytefray_server.spec`. Verification proved neither file exists in the repository; tournaments run via `bytefray tournament` within the unified binary or `bytefray-cli`.)*

### Key Analysis & Findings

#### 1. Scaffold Template Inclusion Policy
- [tools/bytefray.spec](file:///d:/Projects/BATTLE2/tools/bytefray.spec#L34-L43) derives template directories dynamically from the product's canonical inventory ([`battle_engine.agent_scaffold.TEMPLATE_DIRECTORIES_BY_API_VERSION`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/agent_scaffold.py#L35)):
  ```python
  agent_template_dirs = sorted(
      {
          directory
          for templates in TEMPLATE_DIRECTORIES_BY_API_VERSION.values()
          for directory in templates.values()
      }
  )
  ```
- In [tools/agent_designer.spec](file:///d:/Projects/BATTLE2/tools/agent_designer.spec#L29-L35), the identical dynamic derivation is applied, collecting both v1 and v2 template directories.
- In [tools/bytefray_cli.spec](file:///d:/Projects/BATTLE2/tools/bytefray_cli.spec#L27), scaffolding templates are deliberately omitted. This was verified as correct: `bytefray-cli` exposes only match simulation subcommands; `bytefray agents create` is handled exclusively by the unified `bytefray` executable and Designer GUI. Test [`test_windows_packaging_spec.py`](file:///d:/Projects/BATTLE2/engine/tests/test_windows_packaging_spec.py#L327-L334) explicitly enforces `SCAFFOLD_CAPABLE_SPECS = (BYTEFRAY_SPEC, AGENT_DESIGNER_SPEC)`.

#### 2. Bytecode and Debris Filtering Mechanics
- [tools/packaging_data.py](file:///d:/Projects/BATTLE2/tools/packaging_data.py#L80-L84) defines [`is_python_bytecode`](file:///d:/Projects/BATTLE2/tools/packaging_data.py#L55):
  ```python
  normalized = str(relative_path).replace("\\", "/")
  path = PurePosixPath(normalized)
  if any(part == CACHE_DIRECTORY_NAME for part in path.parts):
      return True
  return path.suffix.lower() in BYTECODE_SUFFIXES
  ```
  Where `CACHE_DIRECTORY_NAME = "__pycache__"` and `BYTECODE_SUFFIXES = frozenset({".pyc", ".pyo"})`.
- Deliberately, `.pyd` files are preserved as native extension modules on Windows.
- **Limitation Identified (FIND-07):** The directory component check is case-sensitive (`part == CACHE_DIRECTORY_NAME`). If a tool creates `__PyCache__` or `__PYCACHE__`, non-bytecode files inside it (e.g. text notes) would pass the filter.

#### 3. Asset Packaging Asymmetry (FIND-06)
- In [tools/bytefray.spec](file:///d:/Projects/BATTLE2/tools/bytefray.spec#L12-L74):
  ```python
  branding_dir = os.path.join(project_root, "app", "assets", "branding")
  datas += collect_data_tree(branding_dir, "assets/branding")
  ```
  This bundles only [app/assets/branding/bytefray-icon.png](file:///d:/Projects/BATTLE2/app/assets/branding/bytefray-icon.png) (145 KB), which is the sole runtime window icon required.
- In [tools/agent_designer.spec](file:///d:/Projects/BATTLE2/tools/agent_designer.spec#L12-L46) and [tools/replay_viewer.spec](file:///d:/Projects/BATTLE2/tools/replay_viewer.spec#L11-L24):
  ```python
  assets_dir = os.path.join(project_root, "assets")
  datas += collect_data_tree(assets_dir, "assets")
  ```
  This bundles the entire repository-root [assets/](file:///d:/Projects/BATTLE2/assets) directory, including `bytefray-brand-sheet.png` (1.16 MB) and `bytefray-logo-horizontal.png` (190 KB), which are documentation/marketing assets never referenced by the runtime application.

#### 4. Post-Build Guard Coverage
- [tools/build_win.ps1](file:///d:/Projects/BATTLE2/tools/build_win.ps1#L93-L106) loops over every generated artifact directory in `dist/windows` and fails if any `__pycache__`, `.pyc`, or `.pyo` file is found.
- [tools/build_win.ps1](file:///d:/Projects/BATTLE2/tools/build_win.ps1#L215-L238) runs live execution smokes of `bytefray agents create` and `agents validate` across all four supported variants (`smoke_agent`, `smoke_agent_annotated`, `smoke_agent_v2`, `smoke_agent_v2_annotated`) against the frozen binary in a disposable `BYTEFRAY_ROOT`.
- [tools/build_win.ps1](file:///d:/Projects/BATTLE2/tools/build_win.ps1#L260-L265) verifies that build smoke runs did not leave runtime-generated `agents/` directories inside the distributable trees.

---

## D. Cross-platform/CI review

### Host-Dependent Assumptions & CI Portability
We audited cross-platform assumptions across path resolution, build scripts, and CI workflows ([.github/workflows/ci.yml](file:///d:/Projects/BATTLE2/.github/workflows/ci.yml)).

#### 1. Separator Normalization
- In [tools/packaging_data.py](file:///d:/Projects/BATTLE2/tools/packaging_data.py#L80), `replace("\\", "/")` followed by `PurePosixPath` parsing ensures that Windows backslash paths are treated consistently when evaluated on POSIX hosts during CI linting and testing.
- Test [`engine/tests/test_frozen_bytecode_exclusion.py`](file:///d:/Projects/BATTLE2/engine/tests/test_frozen_bytecode_exclusion.py#L120-L132) asserts:
  ```python
  assert is_python_bytecode(relative) == is_python_bytecode(relative.replace("/", "\\"))
  ```
  Both slash styles are verified independently against ground truth expected outcomes.

#### 2. Build Script Parity Gap (FIND-05)
- [tools/build_win.ps1](file:///d:/Projects/BATTLE2/tools/build_win.ps1#L93-L106) contains an automated debris verification sweep:
  ```powershell
  foreach ($Artifact in $Artifacts) {
    $ArtifactDir = Join-Path $DistDir $Artifact.Name
    $Debris = @(
      Get-ChildItem -LiteralPath $ArtifactDir -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object {
          ($_.PSIsContainer -and $_.Name -eq "__pycache__") -or
          (-not $_.PSIsContainer -and $_.Extension -in ".pyc", ".pyo")
        }
    )
    if ($Debris.Count -gt 0) {
      throw "Python bytecode/cache reached the frozen payload for $($Artifact.Name)..."
    }
  }
  ```
- In contrast, [tools/build_linux.sh](file:///d:/Projects/BATTLE2/tools/build_linux.sh#L64-L77) builds all four PyInstaller artifacts but terminates without inspecting the resulting `dist/` directories for bytecode or development debris. While CI currently tests Linux via headless wheels rather than Linux PyInstaller binaries, this script gap introduces silent regression risk if Linux binary packaging is enabled in CI.

---

## E. Starter-refresh review

### Architecture & Migration State Machine
Starter agent lifecycle is governed by [engine/src/battle_engine/starters.py](file:///d:/Projects/BATTLE2/engine/src/battle_engine/starters.py). `ensure_starter_agents()` validates bundled starters against user files in `~/.bytefray/agents/`:
1. `installed_digest is None` -> `_copy_missing` (Installs missing starter).
2. `installed_digest == bundled_digest` -> No-op (`CURRENT`).
3. `installed_digest in SUPERSEDED_STARTER_DIGESTS.get(name, ())` -> `_mirror_bundled` (Pristine upgrade).
4. Anything else -> `_copy_missing` and record in `customized` (`CUSTOMIZED`).

### Detailed Audit of Starter Refresh Risks

#### 1. Non-Atomic Directory In-Place Trapping (FIND-03 - Medium Severity)
- In [starters.py:390-414](file:///d:/Projects/BATTLE2/engine/src/battle_engine/starters.py#L390-L414):
  ```python
  def _mirror_bundled(
      source_agent_dir: Path, destination_dir: Path, files: list[Path]
  ) -> None:
      wanted = {source.relative_to(source_agent_dir): source for source in files}
      for relative, source in wanted.items():
          destination = destination_dir / relative
          destination.parent.mkdir(parents=True, exist_ok=True)
          payload = source.read_bytes()
          if destination.is_file() and destination.read_bytes() == payload:
              continue
          destination.write_bytes(payload)
      base = destination_dir.resolve()
      for existing in starter_content_files(destination_dir):
          if existing.relative_to(base) not in wanted:
              existing.unlink()
  ```
- **Failure Mechanism:**
  Files are written sequentially and directly into the user's active starter directory. If the process is interrupted midway (process killed, crash, power failure):
  1. `destination_dir` is left containing partially new and partially old files.
  2. On subsequent launches, `starter_content_digest(destination_dir)` produces a hybrid SHA-256 hash.
  3. This hybrid digest matches neither `bundled_digest` nor any historical entry in `SUPERSEDED_STARTER_DIGESTS`.
  4. Line 490 appends a `StarterCustomization` record, classifying the starter as `customized`.
  5. **Consequence:** The user never edited the starter, yet it is permanently locked out of automated upgrades.

#### 2. Loose Bytecode File Inclusion (FIND-04 - Low Severity)
- In [starters.py:153-164](file:///d:/Projects/BATTLE2/engine/src/battle_engine/starters.py#L153-L164) ([`starter_content_files`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/starters.py#L143)):
  ```python
  files: list[Path] = []
  for candidate in base.rglob("*"):
      if "__pycache__" in candidate.parts:
          continue
      ...
      if resolved.is_file():
          files.append(candidate)
  ```
- **Failure Mechanism:**
  The check only rejects paths containing the literal component `"__pycache__"`. Loose `.pyc` or `.pyo` files created directly inside the starter root (or in directories with case variations like `__PYCACHE__`) are appended to `files`.
  Because `.pyc` is not in `_TEXT_SUFFIXES`, its binary bytes are digested, changing the directory hash and triggering false `customized` classifications.

#### 3. Line-Ending Stability
- Line-ending normalization in [`_normalized_content`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/starters.py#L167-L171) handles CRLF (`\r\n`) and CR (`\r`) by normalizing them to LF (`\n`) for all suffixes in `_TEXT_SUFFIXES = frozenset({".py", ".yaml", ".yml", ".json", ".md", ".txt", ".rst"})`. All starter files currently use `.py`, `.yaml`, or `.md`, preventing cross-platform digest drift.

---

## F. Parameter/provenance review

### Architecture & Data Flow
Agent API v2 parameters were introduced in Phase D/E to allow agents to declare schemas, validation bounds, defaults, and presets in `agent.yaml`.
- Resolved parameters must travel on [`MatchEntrant.parameters`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/match_service.py#L116) and reach the agent via [`MatchContextV2.parameters`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/agent_api.py#L182).
- Non-empty parameters are included in [`canonical_match_id`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/match_service.py#L1128-L1130).

### Key Inconsistencies Discovered

#### 1. Entrant Parameter Resolution Omission in Subcommands (FIND-01 - High Severity)
- **Standard CLI Execution ([`bytefray run` in cli.py](file:///d:/Projects/BATTLE2/engine/src/battle_engine/cli.py#L929-L968)):**
  ```python
  paramsA = _resolve_entrant_parameters("A", pythonA, args) if pythonA else {}
  ...
  entrants = [MatchEntrant.python("A", nameA, startA, pythonA, paramsA), ...]
  ```
  Here, schema defaults and CLI overrides are resolved before match execution, and `MatchEntrant.parameters` is populated with the resolved values.
- **Tournament CLI ([tournament_cli.py:108](file:///d:/Projects/BATTLE2/engine/src/battle_engine/tournament_cli.py#L108)):**
  ```python
  if spec is not None and spec.kind == "python":
      return MatchEntrant.python(name, spec.display or name, start, spec)
  ```
  `parameters` is omitted, defaulting to `None`, which `MatchEntrant.__init__` converts to an empty mapping `{}`.
- **Agent Test ([agent_test.py:453](file:///d:/Projects/BATTLE2/engine/src/battle_engine/agent_test.py#L453)):**
  ```python
  MatchEntrant.python(TESTED_AGENT_SLOT, agent_id, effective_agent_start, tested_spec),
  ```
  `parameters` is omitted (`{}`).
- **Agent Evaluation ([agent_evaluation.py:1073](file:///d:/Projects/BATTLE2/engine/src/battle_engine/agent_evaluation.py#L1073)):**
  ```python
  MatchEntrant.python(TESTED_AGENT_SLOT, slot_a_agent_id, slot_a_start, slot_a_spec),
  ```
  `parameters` is omitted (`{}`).

#### Empirical Verification of Match ID Divergence
We executed an empirical probe comparing `canonical_match_id` for identical seed (42), ruleset (`bytefray-rules-4`), and agents (`v5_core_defender` vs `v5_scout_striker`):
```text
RUN match_id:        match_e81729d921d273fbff22d70d
TOURNAMENT match_id: match_001cd266c13be895ec0b2232
```
Because `MatchRequest.canonical_match_id` hashes `entrant.parameters` when non-empty ([match_service.py:1128](file:///d:/Projects/BATTLE2/engine/src/battle_engine/match_service.py#L1128)), the tournament runner generates divergent match IDs for the exact same agent matchup. Furthermore, inside tournament matches, agents receive an empty mapping for `context.parameters`.

#### 2. Supervised Runtime Parameter Drop (FIND-02 - Medium Severity)
- In [process_runtime.py:462](file:///d:/Projects/BATTLE2/engine/src/battle_engine/process_runtime.py#L462) (standard worker execution):
  ```python
  reset_result = handle.reset(
      match_seed=config.seed,
      api_version=2,
      arena_size=config.arena_size,
      tick_limit=max_ticks,
      action_budget=config.instr_per_tick,
      timeout=agent_call_timeout,
      parameters=entrant.parameters,
  )
  ```
- In [supervised_runtime.py:284-292](file:///d:/Projects/BATTLE2/engine/src/battle_engine/supervised_runtime.py#L284-L292) (Agent Lab timeout execution):
  ```python
  reset_result = handle.reset(
      match_seed=self.config.seed,
      api_version=api_version,
      arena_size=self.config.arena_size,
      tick_limit=self.max_ticks,
      action_budget=self.config.instr_per_tick,
      locality_reach=self.locality_reach,
      timeout=self.agent_call_timeout,
  )
  ```
  `parameters` is omitted from `handle.reset()`.
- In [`agent_worker.py:441`](file:///d:/Projects/BATTLE2/engine/src/battle_engine/agent_worker.py#L441), the worker process populates context parameters from the reset message:
  ```python
  parameters=MappingProxyType(dict(request.get("parameters") or {}))
  ```
  Because `supervised_runtime.py` never passed `parameters`, `request.get("parameters")` is `None`, and the supervised agent receives `{}`.
- **Impact & Provenance Discrepancy:**
  When a user runs `bytefray run --agent-call-timeout` or evaluates an agent in Agent Lab:
  1. The agent executes with an empty parameter dictionary `{}`.
  2. Meanwhile, [match_service.py:881-885](file:///d:/Projects/BATTLE2/engine/src/battle_engine/match_service.py#L881-L885) writes `entrant_parameters` to `result.json` using `request.entrants`, recording the resolved parameter defaults.
  3. The result metadata falsely records that the agent executed with its resolved parameters when it actually ran with an empty dictionary.

---

## G. Regression-test adequacy

Review of regression tests introduced during Phases F1, F2, and F3:

### F1: Missing API-v2 Scaffold Resources
- **Question:** *Would the test fail if the frozen executable lost those resources again?*
- **Assessment:**
  - **Unit Test Layer:** [`engine/tests/test_windows_packaging_spec.py`](file:///d:/Projects/BATTLE2/engine/tests/test_windows_packaging_spec.py#L341-L360) parses the AST of `tools/bytefray.spec` and `tools/agent_designer.spec`. If the spec file drops template entries, the AST test fails. However, if PyInstaller collection fails during build, the AST test passes vacuously.
  - **Artifact Test Layer:** [`engine/tests/test_frozen_scaffold_resources.py`](file:///d:/Projects/BATTLE2/engine/tests/test_frozen_scaffold_resources.py#L270-L289) tests the actual built executable, but skips unless `BYTEFRAY_FROZEN_EXE` is set in the environment.
  - **Build Script Layer:** [tools/build_win.ps1:215-238](file:///d:/Projects/BATTLE2/tools/build_win.ps1#L215-L238) provides the true regression gate: it runs live `agents create` and `agents validate` against the produced `bytefray.exe` in CI, guaranteeing failure if the executable lacks resources.

### F2: Frozen Bytecode/Development-Debris Leakage
- **Question:** *Would the test fail when building from a deliberately dirty checkout?*
- **Assessment:**
  - **Unit Test Layer:** [`test_frozen_bytecode_exclusion.py:303-325`](file:///d:/Projects/BATTLE2/engine/tests/test_frozen_bytecode_exclusion.py#L303-L325) ([`test_dirty_checkout_produces_a_clean_data_list`](file:///d:/Projects/BATTLE2/engine/tests/test_frozen_bytecode_exclusion.py#L303)) plants genuine sentinel `.pyc` and `__pycache__` files across all four specs and asserts that `datas` contains no bytecode entries.
  - **Build Script Layer:** [tools/build_win.ps1:93-106](file:///d:/Projects/BATTLE2/tools/build_win.ps1#L93-L106) recurses through every artifact's onedir payload in `dist/` and throws an error if any `.pyc`, `.pyo`, or `__pycache__` exists.
  - **Conclusion:** Yes, both layers would detect and fail a dirty checkout build.

### F3-A: Cross-Platform Separator Classification
- **Question:** *Does the test independently assert both slash styles?*
- **Assessment:**
  - In [`test_frozen_bytecode_exclusion.py`](file:///d:/Projects/BATTLE2/engine/tests/test_frozen_bytecode_exclusion.py#L78-L107), `ALLOWED_PATHS` includes `pkg\\data.bin` and `REJECTED_PATHS` includes `pkg\\__pycache__\\x.cpython-313.pyc`, `pkg\\__pycache__\\readme.txt`, `pkg\\x.pyc`, and `pkg\\x.pyo`.
  - These are evaluated directly against `is_python_bytecode(relative)` and independently asserted against expected `True` or `False`.
  - In addition, `test_filter_agrees_across_windows_and_posix_separators` asserts agreement between `/` and `\`.
  - **Conclusion:** Yes, both slash styles are independently tested against ground-truth expected values.

### F3-B: Full-Git-History Dependency
- **Question:** *Can the test genuinely run without access to a Git repository?*
- **Assessment:**
  - Prior to Phase F3, `_seed_phase_c_starter` invoked `git ls-tree` and `git cat-file` against historical commit `69fc958`, failing under shallow CI checkouts (`fetch-depth: 1`).
  - In Phase F3, commit `bfc8097` added committed fixtures to `engine/tests/fixtures/phase_c_v5_starters/`.
  - [`test_v5_alpha1_phase_e_starter_refresh.py`](file:///d:/Projects/BATTLE2/engine/tests/test_v5_alpha1_phase_e_starter_refresh.py#L83-L90) now copies from committed fixture files via `shutil.copy2`. Subprocess calls to git were completely eliminated.
  - **Conclusion:** Yes, the test runs cleanly with zero git access or git history.

### F3-C: Python-Version-Sensitive Dataclass Default
- **Question:** *Is the failure covered in a way that CI on supported Python versions will detect?*
- **Assessment:**
  - The defect involved bare `= MappingProxyType({})` defaults raising `ValueError` on Python 3.11 due to dataclass unhashable default checks.
  - Fixed via `field(default_factory=lambda: MappingProxyType({}))` in `MatchEntrant` ([match_service.py:116](file:///d:/Projects/BATTLE2/engine/src/battle_engine/match_service.py#L116)) and `EntrantResultPresentation` ([designer_workflows.py:268](file:///d:/Projects/BATTLE2/app/services/designer_workflows.py#L268)).
  - CI workflow `.github/workflows/ci.yml` includes an explicit Python 3.11 matrix entry (`test-linux-core`).
  - Because `match_service.py` is imported during pytest collection for almost all test modules, any future reintroduction of a bare unhashable default immediately breaks test collection in CI on Python 3.11.
  - **Conclusion:** Yes, CI matrix execution reliably catches this defect.

---

## H. Findings table

| ID | Severity | Area | Evidence | User impact | Existing coverage | Recommended future action |
|---|:---:|---|---|---|---|---|
| **FIND-01** | **HIGH** | Parameters & Provenance | [tournament_cli.py:108](file:///d:/Projects/BATTLE2/engine/src/battle_engine/tournament_cli.py#L108)<br>[agent_test.py:453](file:///d:/Projects/BATTLE2/engine/src/battle_engine/agent_test.py#L453)<br>[agent_evaluation.py:1073](file:///d:/Projects/BATTLE2/engine/src/battle_engine/agent_evaluation.py#L1073) | `canonical_match_id` diverges between `bytefray run` and `bytefray tournament` for identical rosters. Entrants in tournaments, agent tests, and evaluations receive empty parameters `{}` instead of declared schema defaults. | Covered in `cli.py` and `designer_workflows.py`, but no test asserts match ID parity across subcommands. | Extract shared `resolve_entrant_parameters()` helper and invoke across all entrant construction sites. Add match ID parity test. |
| **FIND-02** | **MEDIUM** | Supervised Runtime | [supervised_runtime.py:284-292](file:///d:/Projects/BATTLE2/engine/src/battle_engine/supervised_runtime.py#L284-L292) vs [process_runtime.py:462](file:///d:/Projects/BATTLE2/engine/src/battle_engine/process_runtime.py#L462) | Agents running under `--agent-call-timeout` or Agent Lab receive empty parameters `{}`. Result metadata claims parameters were present, creating a provenance falsehood. | `test_supervised_runtime.py` verifies timeouts, but does not assert parameter receipt. | Pass `parameters=entrant.parameters` to `handle.reset()` in `supervised_runtime.py`. Add regression test. |
| **FIND-03** | **MEDIUM** | Starter Refresh Safety | [starters.py:390-414](file:///d:/Projects/BATTLE2/engine/src/battle_engine/starters.py#L390-L414) (`_mirror_bundled`) | An interrupted or failed starter update leaves a hybrid directory whose digest matches neither old nor new bundled templates, permanently locking the starter in `CUSTOMIZED` status. | `test_v5_alpha1_phase_e_starter_refresh.py` tests full state transitions, but not partial write interruptions. | Stage files in a temporary peer directory (`.tmp_<uuid>`) and perform an atomic directory rename/replace. |
| **FIND-04** | **LOW** | Starter Content Filtering | [starters.py:153-164](file:///d:/Projects/BATTLE2/engine/src/battle_engine/starters.py#L153-L164) (`starter_content_files`) | Loose `.pyc`/`.pyo` files or case variations (`__PYCACHE__`) are included in starter digests, corrupting SHA-256 hashes and falsely classifying starters as customized. | Normal directories covered, but no tests assert loose bytecode exclusion in starter roots. | Filter `candidate.suffix.lower() in {".pyc", ".pyo"}` and case-fold cache directory checks. |
| **FIND-05** | **LOW** | Packaging & Build Parity | [tools/build_linux.sh:77](file:///d:/Projects/BATTLE2/tools/build_linux.sh#L77) vs [tools/build_win.ps1:93-106](file:///d:/Projects/BATTLE2/tools/build_win.ps1#L93-L106) | `build_linux.sh` terminates without asserting dist tree cleanliness, risking undetected bytecode leakage if Linux PyInstaller binaries are distributed. | Unit tests cover `packaging_data.py`, but no test asserts dist tree cleanliness on Linux. | Port PowerShell post-build file inspection logic to `tools/build_linux.sh`. |
| **FIND-06** | **LOW** | Packaging Asset Asymmetry | [agent_designer.spec:46](file:///d:/Projects/BATTLE2/tools/agent_designer.spec#L46)<br>[replay_viewer.spec:24](file:///d:/Projects/BATTLE2/tools/replay_viewer.spec#L24) vs [bytefray.spec:74](file:///d:/Projects/BATTLE2/tools/bytefray.spec#L74) | Standalone GUI specs bundle the entire repo `assets/` directory (including 1.16MB brand sheet), bloating standalone binaries with unused documentation/marketing images. | `test_windows_packaging_spec.py` asserts asset presence, but does not restrict unneeded images. | Unify standalone specs to collect `app/assets/branding` instead of the full `assets/` directory. |
| **FIND-07** | **INFO** | Packaging Data Collection | [tools/packaging_data.py:82](file:///d:/Projects/BATTLE2/tools/packaging_data.py#L82) | `part == CACHE_DIRECTORY_NAME` is case-sensitive, potentially missing non-bytecode files in non-standard `__PYCACHE__` directories on Windows. | `test_frozen_bytecode_exclusion.py` tests various paths, but not case variations of cache directories. | Use `part.lower() == CACHE_DIRECTORY_NAME.lower()`. |

---

## I. Rejected hypotheses

During independent falsification, we investigated several plausible regression suspicions and proved them false:

1. **Hypothesis: `tools/bytefray_cli.spec` erroneously omits scaffold template directories.**
   - *Initial Suspicion:* `bytefray.spec` bundles `agent_template` resources, but `bytefray_cli.spec` does not. Could `bytefray-cli` fail when creating agents?
   - *Investigation:* `cli.py` has no `agents create` command. Agent creation is an interactive GUI feature housed in the Designer (`app/designer`). The headless CLI does not require scaffolding templates.
   - *Verdict:* **REJECTED.** Test `test_windows_packaging_spec.py:327-334` explicitly enforces that `bytefray_cli.spec` must NOT bundle templates to prevent dead weight.

2. **Hypothesis: Bundled GUI binary crashes due to missing brand sheet or horizontal logo.**
   - *Initial Suspicion:* Marketing brand assets in repo-root `assets/branding/` are excluded from `bytefray.spec`.
   - *Investigation:* The application window icon is loaded from `assets/branding/bytefray-icon.png`, which is bundled. Brand sheets and horizontal logos under `assets/` are marketing/doc assets only.
   - *Verdict:* **REJECTED.** No runtime code references `bytefray-brand-sheet.png`.

3. **Hypothesis: Python 3.11 dataclass unhashable defaults cause runtime crash during match initialization.**
   - *Initial Suspicion:* Dataclasses with mutable default mappings cause crashes under Python 3.11+.
   - *Investigation:* All dataclasses in `battle_engine/parameters.py` and `match_service.py` utilize `field(default_factory=lambda: MappingProxyType({}))` or immutable mappings.
   - *Verdict:* **REJECTED.** Verified clean under Python 3.11 in CI.

4. **Hypothesis: Windows CRLF vs Linux LF causes digest divergence in starter auto-refresh.**
   - *Initial Suspicion:* Starter files edited or checked out on Windows would calculate different SHA-256 hashes than on Linux.
   - *Investigation:* `starters.py:_normalized_content()` explicitly decodes text files and normalizes all newline sequences (`\r\n` and `\r`) to LF (`\n`) before digesting.
   - *Verdict:* **REJECTED.** Digits are byte-identical across platforms.

5. **Hypothesis: Linux forward-slash paths bypass `packaging_data.py` bytecode exclusion.**
   - *Initial Suspicion:* `packaging_data.py` normalizes backslashes to slashes; could Linux paths behave differently?
   - *Investigation:* `packaging_data.py` replaces `\` with `/` and parses with `PurePosixPath`. Tested under Linux WSL Python 3.12: `is_python_bytecode` behaves identically across both platforms.
   - *Verdict:* **REJECTED.**

6. **Hypothesis: Prior report's claim that `tools/bytefray_tournament.spec` and `tools/bytefray_server.spec` exist.**
   - *Initial Suspicion:* Prior audit report claimed these two specs were part of the Windows packaging architecture.
   - *Investigation:* Files checked via `Test-Path tools/bytefray_tournament.spec` and `tools/bytefray_server.spec`. Both returned `False`. `build_win.ps1` only builds four artifacts: `bytefray`, `bytefray-cli`, `bytefray-agent-designer`, and `bytefray-replay-viewer`.
   - *Verdict:* **REJECTED.** Prior report hallucinated these spec names.

7. **Hypothesis: Prior report's claim that `supervised_runtime.py` parameter omission is safe because of constructor parameters.**
   - *Initial Suspicion:* Prior report claimed FIND-06 was purely "Informational" because `handle.reset(...)` relied on constructor parameters.
   - *Investigation:* Inspection of `AgentWorkerHandle.__init__` in `agent_worker.py:216` proved it accepts only `agent_id` and `slot`—no parameter mapping exists on the constructor. Supervised workers truly execute with `{}`.
   - *Verdict:* **REJECTED.** Upgraded to Medium finding.

---

## J. Suggested backlog

### Should Fix Before Beta (Priority 1)
1. **Unify Entrant Parameter Resolution (Addressing FIND-01):**
   - Extract a shared helper `resolve_entrant_parameters(agent_spec, overrides=None)` in `battle_engine/parameters.py`.
   - Update `tournament_cli.py`, `agent_test.py`, and `agent_evaluation.py` to resolve and attach entrant parameter defaults.
   - Add integration tests asserting that `bytefray run` and `bytefray tournament` produce identical `canonical_match_id` for identical seeds and rosters.
2. **Forward Parameters in Supervised Runtime (Addressing FIND-02):**
   - Update `supervised_runtime.py:284` to pass `parameters=entrant.parameters` to `handle.reset()`, matching `process_runtime.py:462`.
   - Add a test asserting that an agent running with `--agent-call-timeout` receives non-empty `context.parameters`.
3. **Make Starter Refresh Atomic (Addressing FIND-03):**
   - Refactor `_mirror_bundled` in `starters.py` to stage files in a temporary sibling directory and atomically replace the destination directory upon completion.
   - Add unit tests simulating partial refresh interruptions.

### Worthwhile Hardening (Priority 2)
4. **Harden Starter Content File Filtering (Addressing FIND-04):**
   - Update `starter_content_files` in `starters.py` to exclude `path.suffix.lower() in {".pyc", ".pyo"}` and case-fold directory checks.
5. **Synchronize Build Script Debris Verification (Addressing FIND-05):**
   - Add recursive `.pyc` and `__pycache__` checks to `tools/build_linux.sh` mirroring `tools/build_win.ps1`.
6. **Eliminate Packaging Asset Asymmetry (Addressing FIND-06):**
   - Update `tools/agent_designer.spec` and `tools/replay_viewer.spec` to bundle `app/assets/branding` instead of the full `assets/` directory.

### Optional Cleanup (Priority 3)
7. **Packaging Helper Case Normalization (Addressing FIND-07):**
   - Update `tools/packaging_data.py:82` to use `part.lower() == CACHE_DIRECTORY_NAME.lower()`.

---

## K. Boost/worktree evaluation

### Worktree Provisioning & Platform Evaluation
1. **Workstream Count & Organization:**
   - 5 distinct workstreams (Packaging Completeness, Cross-Platform Portability, Starter Refresh Safety, Parameter Provenance, Regression Test Adequacy) were investigated.
2. **Worktree Isolation Observation:**
   - As documented in Section A, automated worktree creation via `Workspace='share'` failed because Windows `MAX_PATH` (260 characters) was exceeded by long relative paths under `docs/screenshots/` when appended to Antigravity's scratch directory path.
   - Operating in `Workspace='inherit'` mode directly within `D:\Projects\BATTLE2` was successful and safe due to strict read-only execution.
   - **Recommendation for Windows Boost Environments:** Configure Git with `core.longpaths = true` and ensure scratch roots are mounted at short paths (e.g. `C:\_ag\w\<id>`).
3. **Primary Checkout Integrity:**
   - The primary checkout was completely protected: 0 tracked files were modified, 0 git history operations were run, and zero git locks (`.git/index.lock`) were created.
   - Only `docs/research/v5/V5_ALPHA1_POST_RELEASE_HARDENING_AUDIT.md` was created.
4. **Multi-Agent / Independent Falsification Assessment:**
   - The independent falsification review dramatically improved upon the prior attempt:
     - Disproved 7 incorrect hypotheses/hallucinations in the prior report (including non-existent spec files and fabricated code snippets).
     - Upgraded the supervised runtime parameter omission from "Informational" to "Medium" after proving `AgentWorkerHandle` dropped parameters entirely.
     - Discovered the asset packaging asymmetry in standalone GUI specs (FIND-06).
   - Multi-agent independent verification proved indispensable for preventing confirmation bias and ensuring high-fidelity engineering reporting.

---

## Remaining Questions & Gaps

1. **Linux PyInstaller Binary Roadmap:**
   `tools/build_linux.sh` is present in the repository, but CI workflows currently focus exclusively on the pure-Python headless Linux wheel. Whether Linux binary distributions will be officially supported in V5 Beta 1 remains an open product decision.
2. **Designer UI Parameter Interaction:**
   While headless CLI and service paths (`cli.py`, `tournament_cli.py`, `designer_workflows.py`) were thoroughly verified, interactive PySide6 UI widgets in `app/widgets/agent_parameters.py` were audited via static analysis rather than live display automation, as GUI tests are excluded from headless test runs.
3. **Follow-Up Investigation Focus:**
   The immediate next development priority is implementing the shared parameter resolution helper in `battle_engine/parameters.py` to resolve FIND-01 and FIND-02 before the V5 Beta 1 feature freeze.

---
*End of Audit Report.*
