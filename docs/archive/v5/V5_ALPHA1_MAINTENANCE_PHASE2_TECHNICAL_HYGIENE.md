# Bytefray V5 Alpha 1 Maintenance — Phase 2: Behavior-Neutral Technical Hygiene

**Status:** Complete. Behavior-neutral executable cleanup only. No gameplay,
Ruleset, Agent API, replay, CLI, Designer UX, or GUI-visible behavior was
changed. No commit or push was performed.
**Discipline:** Each of the seven Phase 2 candidates (FIND-03 through
FIND-07, dead installer `replays`/`logs` handling, dead `EngineRunner`) was
independently re-verified against current HEAD before any change, per
`V5_ALPHA1_MAINTENANCE_PHASE0_BASELINE.md` Section G invariant 15. One
candidate (FIND-03) was deferred rather than forced; every other candidate
was remediated with a minimal diff and focused regression coverage.

---

## A. Starting state

| Item | Value |
|---|---|
| Branch | `v5-research` |
| HEAD SHA (start and end of this phase) | `7ee0e2ffe5d75d53f9971858d135bd7992787618` |
| Upstream/tracking branch | `origin/v5-research` |
| Ahead/behind upstream | `0` / `0` (exactly up to date, both at start and end) |
| Working-tree state at phase start | Clean — `nothing to commit, working tree clean` |
| Product version (`pyproject.toml`) | `5.0.0a1` (unchanged) |

HEAD did not move during this phase (no commit was made). Phase 0's and
Phase 1's reports (`V5_ALPHA1_MAINTENANCE_PHASE0_BASELINE.md`,
`V5_ALPHA1_MAINTENANCE_PHASE1_DOC_REPO_CLEANUP.md`) were both already present
and committed at the start of this phase — no unrelated prior-phase work was
absorbed into this phase's diff, and none needed to be, since the working
tree was clean before this phase's first edit.

---

## B. Behavioral invariants

The full protected-surface table from `V5_ALPHA1_MAINTENANCE_PHASE0_BASELINE.md`
Section D applies unchanged: Ruleset gameplay semantics
(`bytefray-rules-1/2/4/4-alpha1/4-alpha2`), scheduler/process behavior,
Agent API v1/v2 contracts and observation/action semantics, deployment,
mortality, territory/core mechanics, scoring, victory/termination logic,
seeding/determinism, starter *behavior* (as opposed to starter-file
*packaging hygiene*), CLI/Designer defaults and workflows, replay generation/
schema/playback semantics, and Replay Viewer rendering are all
**PROHIBITED DURING FEEDBACK** or **REQUIRES SPECIAL REVIEW** exactly as
Phase 0 recorded them. No change in this phase touches any surface in that
table: every change is confined to (a) removing a class with zero live
callers, (b) a digest-input filter used only for starter-*upgrade*
classification (not starter runtime behavior), (c) two PyInstaller `.spec`
files' packaging-only `datas` scope, (d) a packaging-data helper's
case-sensitivity, (e) an installer's `[Dirs]` list, and (f) a build script's
post-build verification step. For identical ruleset, seed, agents,
parameters, and configuration, match behavior is unchanged — verified in
Section L.

---

## C. FIND-03 disposition

**Original finding** (`V5_ALPHA1_POST_RELEASE_HARDENING_AUDIT.md`, Section E,
"MEDIUM"): `starters.py`'s `_mirror_bundled` (lines 390–413) writes files
sequentially, directly into the user's active starter directory. An
interruption mid-write (crash, kill, power failure) leaves a hybrid
directory whose digest matches neither the old nor the new bundled release,
permanently misclassifying the starter as user-`CUSTOMIZED` and blocking all
future automatic upgrades.

**Current evidence:** Re-verified present at current HEAD —
`engine/src/battle_engine/starters.py`'s `_mirror_bundled` still writes each
file directly to `destination_dir / relative` with no staging directory or
atomic rename. `test_v5_alpha1_phase_e_starter_refresh.py` exercises full
state transitions (missing → installed, superseded → refreshed, customized →
preserved) but has no interruption-simulation test, exactly as
`V5_ALPHA1_MAINTENANCE_PHASE1_DOC_REPO_CLEANUP.md` Section J already
recorded. The finding remains valid.

**Risk classification: UNCERTAIN — DEFER.**

**Reasoning:** The audit's own recommended remediation — stage files in a
temporary sibling directory, then atomically replace the destination — does
not reduce to a small, mechanical change on this repository's primary
platform. Neither Windows nor POSIX offers a single-syscall atomic "replace
a non-empty directory with another non-empty directory"; the closest
practical pattern is a rename-swap (rename the old directory aside, rename
the staged directory into place, then remove the old one), which still has
a real, if brief, window where the destination does not exist at all, and
leaves a genuine new failure mode to reason about: a leftover `.tmp-<uuid>`
or `.old-<uuid>` sibling directory under the user's writable agent catalog
root if cleanup itself is interrupted. Because the catalog root is exactly
the directory the Designer's agent discovery scans, an orphaned staging
directory left behind by a botched atomicity fix could surface as a bogus
entry in the Designer's own agent list — a strictly worse, newly-introduced
observable-behavior regression, not a hygiene improvement. Proving the fix
introduces no such regression would require new interruption-simulation
tests exercising real process-kill timing, which is characterization work
for a fix, not verification of an already-argued-safe minimal change.
Separately, the entire value of this fix is to change what happens in the
interruption case — that is unavoidably a change in observable behavior in
that case (by design), which sits uneasily with this phase's own "no
observable behavior change" mandate even though the *normal* (uninterrupted)
case would remain byte-identical. Given Section 7's explicit instruction
("If any candidate cannot be proven behavior-neutral, defer it instead of
changing it"), FIND-03 is deferred, not implemented.

**Files changed:** none.
**Focused validation:** none (no change made). The existing
`test_v5_alpha1_phase_e_starter_refresh.py` suite (25 tests, including the
new FIND-04 test — Section D below) continues to pass unmodified, confirming
this deferral did not silently drift the surrounding module.

---

## D. FIND-04 disposition

**Original finding** (Section E, "LOW"): `starter_content_files`
(`starters.py:135-164`) excludes `__pycache__` only by an exact-case
directory-name match, and does not filter loose `.pyc`/`.pyo` files that
were never inside a cache directory at all — either would corrupt the
SHA-256 content digest used to classify a starter as `CURRENT`/`SUPERSEDED`/
`CUSTOMIZED`.

**Current evidence:** Re-verified present at current HEAD — the pre-fix
check was exactly `if "__pycache__" in candidate.parts: continue`, with no
suffix filter. The bundled `starter_agents/` tree was confirmed clean of any
stray `.pyc`/`.pyo`/case-variant-cache content at HEAD (a repository-wide
`find` for those patterns under
`engine/src/battle_engine/data/starter_agents` returned zero matches), so the
gap is real but latent for the shipped resource tree today.

**Risk classification: SAFE WITH FOCUSED REGRESSION TEST.**

**Reasoning:** This filter only affects (a) which bundled files get copied
into a user's catalog and (b) which files feed the customization-detection
digest — it has no effect on any starter's runtime behavior, gameplay,
Agent API surface, or CLI/GUI-visible output. Because the current bundled
tree contains none of the file shapes this filter newly excludes, the fix is
provably byte-identical for every currently-shipped starter (confirmed by
`test_current_bundled_content_matches_its_pinned_digest`, which pins every
`CURRENT_STARTER_DIGESTS` value and would fail loudly if any digest moved —
it did not). The only behavior this changes is for a hypothetical installed
copy that already has stray bytecode or a case-variant cache directory,
where the fix strictly improves classification accuracy (fewer false
`CUSTOMIZED` results), never the reverse.

**Proposed minimal remediation:** case-fold the `__pycache__` directory-name
comparison, and add a case-insensitive `.pyc`/`.pyo` suffix check, mirroring
`tools/packaging_data.py`'s own case-insensitive suffix rule (kept as a
separate, independent implementation rather than an import, since
`engine/src/battle_engine` must not depend on `tools/`).

**Implemented.** `engine/src/battle_engine/starters.py`: added
`_BYTECODE_SUFFIXES = frozenset({".pyc", ".pyo"})` and changed
`starter_content_files`'s loop to
`if any(part.lower() == "__pycache__" for part in candidate.parts): continue`
followed by `if candidate.suffix.lower() in _BYTECODE_SUFFIXES: continue`.
Docstring updated to state the case-insensitivity explicitly.

**Files changed:**
- `engine/src/battle_engine/starters.py` (fix).
- `engine/tests/test_v5_alpha1_phase_e_starter_refresh.py` (new regression
  test `test_digest_ignores_loose_bytecode_and_case_variant_cache_dirs`).

**Focused validation:** `python -m pytest engine/tests/test_v5_alpha1_phase_e_starter_refresh.py`
— **25 passed** (24 pre-existing + 1 new), including
`test_current_bundled_content_matches_its_pinned_digest`, proving the
current bundled starters' digests are unaffected.

---

## E. FIND-05 disposition

**Original finding** (Section D, "LOW"): `tools/build_linux.sh` builds all
four PyInstaller artifacts but never inspects the resulting `dist/` trees for
bytecode/cache debris, unlike `tools/build_win.ps1`'s equivalent post-build
sweep.

**Current evidence:** Re-verified present at current HEAD — `build_linux.sh`
proceeds straight from the build loop to the branding-icon check with no
debris scan. Linux PyInstaller binaries are not currently CI-gated or
released (per the audit and `.github/workflows/ci.yml`, which tests Linux
only via the headless wheel), so today's exposure is latent, not shipping.

**Risk classification: SAFE.**

**Reasoning:** This is a pure build-script addition with no runtime,
gameplay, CLI, or GUI effect whatsoever — it only makes a currently
non-gated build script fail loudly if debris ever reaches a Linux frozen
payload, mirroring an already-shipped, already-trusted Windows check
line-for-line. There is no existing behavior for it to change.

**Implemented.** Added a debris-scan loop immediately after the four-artifact
build loop and before the existing branding-icon check, using `find` to
locate any `__pycache__` directory or `.pyc`/`.pyo` file under each
artifact's `dist/linux/<name>` tree and `die`ing with a listing if found —
the same "fail the build, do not silently clean" posture
`build_win.ps1`'s equivalent check uses.

**Files changed:** `tools/build_linux.sh`.

**Focused validation:** `bash -n tools/build_linux.sh` — syntax-clean. A
real Linux PyInstaller build was **not** run as evidence: this development
machine is Windows-only, Linux binary builds are not part of this
repository's current release surface, and running one is release-engineering
work disproportionate to a five-line additive check — recorded here as a
limitation rather than silently assumed complete. The check is structurally
identical to `build_win.ps1`'s already-qualified equivalent, which *is*
exercised on every Windows release build.

---

## F. FIND-06 disposition

**Original finding** (Section C, "LOW"): `tools/agent_designer.spec` and
`tools/replay_viewer.spec` each bundle the entire repository-root `assets/`
directory (`collect_data_tree(assets_dir, "assets")`), including the
1.16MB `bytefray-brand-sheet.png` and 190KB `bytefray-logo-horizontal.png`
marketing images that no runtime code loads, instead of only
`app/assets/branding` the way `tools/bytefray.spec` already does.

**Current evidence:** Re-verified present at current HEAD in both spec
files. Traced the actual runtime resource lookup:
`battle_engine.paths.get_branding_icon_path()` checks
`<resource_root>/assets/branding/<filename>` first, then
`<resource_root>/app/assets/branding/<filename>` as a wheel-install fallback.
`tools/bytefray.spec` already collects `app/assets/branding` (source) into
the `"assets/branding"` (destination) — i.e. it *remaps* the smaller
app-local copy onto the same canonical destination path
`get_branding_icon_path()`'s first candidate checks, rather than bundling the
full repository-root tree. Confirmed no runtime code anywhere in `app/` or
`client/` references `bytefray-brand-sheet.png` or
`bytefray-logo-horizontal.png` (repository-wide grep, zero hits outside the
`.spec`/`.iss` files themselves) — matching the audit's own rejected
hypothesis #2.

**Risk classification: SAFE WITH FOCUSED REGRESSION TEST.**

**Reasoning:** The fix is to make both GUI-only specs do exactly what
`bytefray.spec` already does and has already shipped successfully: collect
`app/assets/branding` at destination `"assets/branding"`. Because the
destination path is unchanged, `get_branding_icon_path()`'s resolution is
byte-for-byte identical before and after — the same file
(`bytefray-icon.png`) lands at the same frozen path
(`_internal/assets/branding/bytefray-icon.png`). Only the two unused
marketing images stop being bundled. No existing test asserted the full
`assets/` directory was required for either spec (confirmed by inspection of
`test_windows_packaging_spec.py` before this change), so no test's expected
result needed to change to accommodate this fix.

**Implemented.** `tools/agent_designer.spec` and `tools/replay_viewer.spec`:
replaced `assets_dir = os.path.join(project_root, "assets")` /
`collect_data_tree(assets_dir, "assets")` with
`branding_dir = os.path.join(project_root, "app", "assets", "branding")` /
`collect_data_tree(branding_dir, "assets/branding")`, matching
`tools/bytefray.spec`'s pattern, with a comment explaining why the
destination path is deliberately unchanged.

**Files changed:**
- `tools/agent_designer.spec` (fix).
- `tools/replay_viewer.spec` (fix).
- `engine/tests/test_windows_packaging_spec.py` (new parametrized regression
  test `test_standalone_gui_specs_bundle_only_the_branding_icon`, asserting
  both specs still bundle `assets/branding/bytefray-icon.png` and no longer
  bundle either marketing asset at any of its possible pre-fix destination
  paths).

**Focused validation:** `python -m pytest engine/tests/test_windows_packaging_spec.py`
— **28 passed** (26 pre-existing + 2 new parametrized cases), including
every pre-existing onedir-layout, scaffold-template-bundling, and
branding-icon assertion for all four specs.

---

## G. FIND-07 disposition

**Original finding** (Section C, "INFORMATIONAL"): `tools/packaging_data.py`'s
`is_python_bytecode` checks `part == CACHE_DIRECTORY_NAME`, which is
case-sensitive; a non-standard `__PyCache__`/`__PYCACHE__` directory's
non-bytecode contents would not be excluded by the directory-component rule.

**Current evidence:** Re-verified present at current HEAD, exact code cited
by the audit unchanged.

**Risk classification: SAFE.**

**Reasoning:** `CACHE_DIRECTORY_NAME` is the fixed literal `"__pycache__"`,
which CPython always writes in exactly that case — a case variant only
arises from an unusual case-preserving copy/archive tool, never from normal
product operation, exactly as the audit's own rejected-hypothesis analysis
(Section I, item 5 in the audit) already established for the adjacent
separator-normalization question. Case-folding the comparison cannot change
the classification of any path this function is actually invoked against
today; it only closes a defensive gap for a scenario that has never
occurred in this repository's build history.

**Implemented.** `tools/packaging_data.py`: changed
`if any(part == CACHE_DIRECTORY_NAME for part in path.parts)` to
`if any(part.lower() == CACHE_DIRECTORY_NAME for part in path.parts)`
(`CACHE_DIRECTORY_NAME` is already all-lowercase, so this is a pure
case-fold with no other behavior change).

**Files changed:**
- `tools/packaging_data.py` (fix).
- `engine/tests/test_frozen_bytecode_exclusion.py` (two new entries in the
  existing `REJECTED_PATHS` parametrization table: `"__PYCACHE__/notes.txt"`
  and `"nested/__PyCache__/agent.cpython-313.pyc"`, exercising the exact
  "non-bytecode file inside a case-variant cache directory" scenario the
  audit describes, through the same parametrized tests every other rejected
  path already runs through, including the Windows/POSIX separator-agreement
  check).

**Focused validation:** `python -m pytest engine/tests/test_frozen_bytecode_exclusion.py`
— **74 passed, 1 skipped** (70 passed pre-existing + 4 new parametrized
cases: 2 new paths × 2 parametrized test functions each already consuming
`REJECTED_PATHS`).

---

## H. `EngineRunner` disposition

**Re-verification of zero callers:** Phase 1 (`V5_ALPHA1_MAINTENANCE_PHASE1_DOC_REPO_CLEANUP.md`
Section G) already corrected Phase 0's initial "load-bearing" conclusion and
established, via two independent full-repository greps, that `EngineRunner`
(`app/services/engine.py`) has zero instantiations anywhere in the tracked
tree, and that the two test files citing it
(`test_designer_third_entrant_command.py`, `test_pmars.py`) only mention it
in a docstring/comment, never call or construct it. This phase re-ran the
identical searches (`EngineRunner`, `EngineRunner(`) against current HEAD
and confirmed the conclusion is unchanged — no new caller was introduced
between Phase 1 and Phase 2.

**One additional coupling this phase found that Phase 0/1 did not fully
trace:** `app/services/engine.py` is not *only* `EngineRunner`'s home — it
also re-exports `RunConfig` and `open_pygame_client_direct` (both actually
*defined* in `app/services/engine_commands.py`) by importing them into its
own namespace. Four production modules import these two names specifically
from `app.services.engine` (not `app.services.engine_commands`):
`app/agent_designer.py`, `app/views/simple.py`, `app/views/advanced.py`, plus
three test files that patch `"app.services.engine.open_pygame_client_direct"`
by that exact dotted path. Deleting the whole module (or the whole import
block) would have broken all of these. `build_engine_command` (the third
name `engine.py` imports from `engine_commands.py`, used only inside
`EngineRunner._build_engine_cmd`) has **no** external importer from
`app.services.engine` — confirmed by a full-repository grep for
`from app.services.engine import` and `app.services.engine\.` — so it was
the one import removable outright.

**Removed:** the `EngineRunner` class itself, and every import that existed
solely for it: `import threading`, `from pathlib import Path`,
`from subprocess import PIPE, STDOUT, Popen`,
`from PySide6.QtCore import QObject, Signal`, `build_engine_command` from the
`engine_commands` import, and the `ensure_dirs`/`get_default_paths` import
from `app.services.osutil` (both remain live elsewhere — `app/views/advanced.py`
still imports them directly from `osutil` — only their unused re-import
inside `engine.py` was removed). Added an explicit `__all__ = ["RunConfig", "open_pygame_client_direct"]`
to `engine.py`, matching this repository's existing re-export convention
(`app/views/evaluation.py`, `app/views/trace_inspector.py`, etc., all mark
intentional re-exports the same way) and keeping `ruff` from flagging the
two remaining imports as unused now that nothing inside the module itself
references them.

**Not touched, per the explicit prohibition against redesigning the
surviving execution path:** `app/agent_designer.py`'s `QProcess`-based match
launch, `engine_commands.py`'s `build_engine_command`/`RunConfig`/
`open_pygame_client_direct` implementations (all three functions/dataclass
are unchanged — only which names `engine.py` re-imports changed), and
`app/services/osutil.py` (unchanged).

**Exact files changed:**
- `app/services/engine.py` — `EngineRunner` class and its solely-owned
  imports removed; `__all__` added. 104 lines removed, 8 lines added (net
  −96 lines; file is now 11 lines).
- `engine/tests/test_designer_third_entrant_command.py` — updated a
  docstring sentence that described `build_engine_command`'s only caller as
  `EngineRunner._build_engine_cmd` (now removed) to state that
  `build_engine_command` has no in-repo production caller left at all and is
  exercised only directly by this test file's own assertions. No test logic
  changed.
- `engine/tests/test_pmars.py` — removed a two-line comment referencing
  `EngineRunner`'s subprocess model as a design parallel (the comment
  described, not tested, the now-removed class; no assertion changed).

**Documentation:** `docs/specs/agent_designer_workflow.md` (a historical
spec document under `docs/specs/`, part of this repository's
spec-before-implementation record per `CONTRIBUTING.md`) already correctly
described `EngineRunner` as dead code "kept for historical reasons" and "a
candidate for removal in an unrelated cleanup pass" at the time it was
written — it does not assert the class is currently live, so no correction
is needed there; it is left unchanged, preserving the historical record of
when and how this was originally identified, per Phase 0 invariant 10.
`docs/archive/v2/V2_0_BETA1_PHASE2_PRODUCT_EXECUTION.md` (a historical
research record) mentions `EngineRunner.finished` in an unrelated,
already-historical context and was likewise left unchanged. No current
(non-historical, non-spec) developer documentation — `ARCHITECTURE.md`
included — mentions `EngineRunner` at all, so no correction was needed
there.

**Surviving Designer execution path (unchanged):** `app/agent_designer.py`'s
own `QProcess`/`QProcessEnvironment`-based match launch, via
`build_designer_match_arguments`, remains the sole live match-launch code
path — exactly as Phase 1 documented and as this phase's own Designer
smoke test (Section L) confirms still starts up correctly.

**Tests:** full focused run below (Section L); no new test was added
specifically for the removal itself, since nothing depended on
`EngineRunner`'s behavior to begin with — only the two stale
comment/docstring references needed correction, and the pre-existing test
suite already covers every surviving name (`build_engine_command`,
`RunConfig`, `open_pygame_client_direct`) directly.

---

## I. Installer `replays` / `logs` disposition

**Lifecycle/reference analysis performed:**
- **Installer definitions:** `tools/installer.iss`'s `[Dirs]` section
  created both `{code:GetDataRoot}\replays` and `{code:GetDataRoot}\logs`
  unconditionally on every install.
- **Runtime path creation/replay storage:** `engine/src/battle_engine/paths.py`'s
  `canonical_replay_directory` resolves replays under
  `root/runs/_designer`, `root/runs/_loose`, or `root/runs` — never a
  top-level `replays/`. A repository-wide grep for the literal directory
  names found no writer anywhere in `engine/`, `app/`, or `client/` for
  either `replays/` or `logs/` as a top-level data-root subdirectory.
- **User-data/config directories, documentation:** `INSTALL.md` mentions
  "agents, replays, summaries, logs, and other data" and "agents, replays,
  history" — confirmed by reading the surrounding prose that these are
  generic *category* descriptions of what survives an uninstall/reinstall
  (actual replay files live under `runs/…`, as above), not a claim that a
  literal `replays/` folder holds them. No documentation correction was
  needed, since no documentation asserts the literal directory is used.
- **Packaging/uninstall:** the installer's `[Registry]`/uninstall behavior
  does not reference either directory by name; Inno Setup's `[Dirs]` entries
  are additive on install and are not deleted on uninstall unless flagged
  otherwise (neither is), so removing a `[Dirs]` line does not touch any
  existing installation's on-disk state.
- **Tests:** `tools/smoke_after_install.ps1`'s `Invoke-InstalledSmoke`
  function is the one piece of tooling this phase found actually *uses*
  these two directories, and it uses them differently:
  - `replays`: checked only for existence
    (`foreach ($WritableDirectory in @("agents", "replays", "logs", "runs\_loose"))`)
    — never written to.
  - `logs`: checked for existence **and** actively written to —
    `$StructureLog = Join-Path $DataRoot "logs\installed-files.txt"` is
    where the smoke script dumps its own post-install file listing.

**Disposition — split, per the asymmetric evidence:**

- **`replays/` — SAFE, removed.** Zero writers anywhere in the tracked tree
  (runtime or tooling); only ever created and existence-checked, never
  written to. Removing its creation is compatibility-safe: it never held
  user data, so there is nothing to migrate, and no existing installation's
  data is affected (Inno Setup does not retroactively delete a
  previously-created empty directory just because a later installer version
  stops creating it).
- **`logs/` — UNCERTAIN, DEFERRED.** Genuinely used — not by the shipped
  application, but by `tools/smoke_after_install.ps1`'s own release-validation
  tooling, which writes its diagnostic file listing there. Removing the
  installer's creation of `logs/` without also relocating that diagnostic
  write would break the installer smoke test itself (a `Set-Content` into a
  non-existent parent directory fails). This is exactly the "required by an
  external packaging convention" / hidden-coupling case Section 5 asks to be
  caught rather than assumed away — Phase 0/1's "no runtime code writes
  there" was correct but incomplete, since it did not check the installer's
  *own validation tooling*. Fixing this properly would mean relocating where
  the smoke test writes its diagnostic output, which is a second, independent
  change to release-validation tooling, not a mechanical installer-only
  deletion — deferred rather than bundled into this phase.

**Changes made:**
- `tools/installer.iss`: removed the `Name: "{code:GetDataRoot}\replays"`
  line from `[Dirs]`; added a comment explaining why (with a pointer to
  `canonical_replay_directory`) and, separately, why `logs` remains.
- `tools/smoke_after_install.ps1`: removed `"replays"` from the
  `$WritableDirectory` existence-check list (`logs` and `agents`/`runs\_loose`
  unchanged) with a matching comment.

**Compatibility considerations:** none for `replays` (see above). `logs` is
untouched, so its existing compatibility posture (including the smoke test's
dependency on it) is unaffected by this phase.

**Tests:** no dedicated unit test exercised `installer.iss`'s `[Dirs]`
contents before this change (confirmed: `test_installer_versions_match_package_and_release_tag`,
the only test reading `INSTALLER_SCRIPT`, checks only version strings). PowerShell
tokenizer syntax-check of the modified `smoke_after_install.ps1` passed
(`[System.Management.Automation.PSParser]::Tokenize` reported zero errors).
A full installer compile + install + uninstall cycle was **not** performed:
`tools/installer.iss`'s `[Files]` section requires a populated
`dist/windows/*` tree from a full four-artifact PyInstaller build, which does
not currently exist in this checkout and would take several minutes to
produce; running an actual `/VERYSILENT` system install additionally
modifies live system state (Program Files, registry, environment variables)
under administrator privileges, which this phase's mandate to avoid
unrelated release work and to treat system-affecting actions carefully both
argue against performing without a separate, explicit release-engineering
task. This is recorded as an open verification gap, not silently assumed
complete — recommended as Phase 3 input (Section O).

---

## J. Protected items explicitly left unchanged

- **`sync_ruleset_choices_for_metadata`** (`app/widgets/ruleset_combo.py:44`)
  — not read, referenced, or modified anywhere in this phase's diff.
- **`--pygame`** (`engine/src/battle_engine/cli.py`) — not read, referenced,
  or modified anywhere in this phase's diff.
- **Tracked qualification agents** (`Nemesis`, `hydra`, `hydra_alpha2`,
  `nemesis_alpha2`, `viper` under repo-root `agents/`) — not touched.
  Untracked/gitignored local agents were likewise not touched (none were
  read, listed, or written by any command this phase ran).
- **Gameplay/Ruleset semantics** — no file under `engine/src/battle_engine`'s
  simulation, scheduler, scoring, termination, deployment, mortality,
  territory, or Agent API modules was modified; the only `engine/src` file
  touched (`starters.py`) affects only starter-*catalog* content-digest
  computation, not match simulation.
- **Replay semantics** — no file under `client/src/battle_client`, no
  replay schema/serialization code, and no replay writer/reader was touched.
- **CLI/Designer/GUI behavior** — no argument parser, default, workflow, or
  widget was modified. The Designer's `QProcess` execution path
  (`app/agent_designer.py`) was read for verification but not edited.

---

## K. Newly discovered technical debt

| Item | Location | Risk | Suggested future phase | Reason not changed now |
| ---- | -------- | ---- | ---------------------- | ---------------------- |
| FIND-03 atomic starter refresh | `engine/src/battle_engine/starters.py:390-413` (`_mirror_bundled`) | Moderate | Future dedicated phase, explicitly scoped for a real fix (not hygiene) | Requires new interruption-simulation control flow whose whole purpose is to change interruption-case behavior, plus cross-platform (Windows/POSIX) directory-replace semantics that risk a new orphaned-directory failure mode if implemented hastily; see Section C |
| Installer `logs/` directory creation | `tools/installer.iss:53`; `tools/smoke_after_install.ps1:138,153` | Low | Release-tooling cleanup phase | `smoke_after_install.ps1` writes its own diagnostic file there; removing the installer's creation requires first relocating that diagnostic write, a second independent change outside "mechanical installer deletion" scope |
| `engine_commands.py`'s `build_engine_command` full removability | `app/services/engine_commands.py:50` | Low | Future Designer-services cleanup phase | Now has zero in-repo *production* callers (its only one, `EngineRunner`, is removed), but it retains substantial direct *test* coverage (`test_launchers.py`, `test_designer_third_entrant_command.py`, `test_v2_default_placement.py`) treating it as a tested unit in its own right; Phase 1 already flagged this as a separate question from `EngineRunner`'s removal, and Phase 2's named candidate was `EngineRunner` only — evaluating whether the function itself should also go is a distinct piece of analysis this phase did not open |
| Full installer build+install+uninstall smoke re-run for the `replays` removal | `tools/installer.iss`, `tools/smoke_after_install.ps1` | Low | Next Windows release-qualification pass | Requires a full four-artifact PyInstaller build (`tools/build_win.ps1`) and an actual system-level installer run under admin privileges; deferred as release-engineering work disproportionate to a one-line, low-risk change — see Section I |
| Real Linux PyInstaller build to exercise the new `build_linux.sh` debris check | `tools/build_linux.sh` | Low | Whenever Linux binary packaging is next exercised (CI or manually) | This development machine is Windows-only; the check was only syntax-validated (`bash -n`), not exercised against a real dirty-checkout build the way `build_win.ps1`'s equivalent already is on every Windows release |

---

## L. Validation

**Focused tests per cleanup item:**

| Item | Command | Result |
|---|---|---|
| `EngineRunner` removal | `pytest engine/tests/test_designer_third_entrant_command.py engine/tests/test_pmars.py engine/tests/test_launchers.py engine/tests/test_v2_default_placement.py tests/test_advanced_panel_ux_labels.py tests/test_agent_designer_lifecycle.py tests/test_replay_browser_initial_directory.py` | **98 passed, 2 skipped** |
| FIND-04 | `pytest engine/tests/test_v5_alpha1_phase_e_starter_refresh.py` | **25 passed** |
| FIND-06 | `pytest engine/tests/test_windows_packaging_spec.py` | **28 passed** |
| FIND-07 | `pytest engine/tests/test_frozen_bytecode_exclusion.py` | **74 passed, 1 skipped** |
| FIND-05 | `bash -n tools/build_linux.sh` | syntax-clean (see Section E for scope limitation) |
| Installer `replays` | PowerShell tokenizer syntax-check of `smoke_after_install.ps1` | zero errors |

**Determinism/equivalence tests:**

| Command | Result |
|---|---|
| `pytest engine/tests -k "v5 or ruleset"` | **732 passed, 2190 deselected** (Phase 0 baseline: 731 passed — the +1 is this phase's new FIND-04 test, which the `v5` keyword filter also matches; 0 new failures) |
| `pytest engine/tests/test_v4_stable_ruleset_equivalence.py` | **23 passed** (the `hydra`/`nemesis`/`hydra_alpha2`/`nemesis_alpha2` tracked-fixture equivalence suite Phase 1 identified as load-bearing) |

**Static analysis:**

| Command | Result |
|---|---|
| `ruff check .` | `All checks passed!` (repo-wide gate; `.spec` files are outside ruff's default target globs and were reviewed by hand instead — see Section F/note below) |
| `mypy engine/src/battle_engine` | `Success: no issues found in 107 source files` |
| `mypy client/src/battle_client` | `Success: no issues found in 16 source files` |

**Packaging/import/startup smoke checks:**

| Check | Result |
|---|---|
| `bytefray --version` | `Bytefray 5.0.0a1, Agent API v2, result schema v1, replay schema v4, Python 3.13.14` — identical to Phase 0's recorded baseline |
| `import app.agent_designer; import app.views.simple; import app.views.advanced` (the three production modules that import from the modified `app.services.engine`) | Imported cleanly, no error |
| Headless Designer GUI startup (`bytefray design` under `QT_QPA_PLATFORM=offscreen`, `BYTEFRAY_GUI_SMOKE_EXIT_MS=750`, isolated `BYTEFRAY_ROOT`) | Exit code `0` |

**Full regression suite:**

`python -m pytest` (canonical headless suite, `pytest.ini`'s default
`-m "not gui"`): **3402 passed, 21 skipped, 3 deselected** in `336.04s`.
Phase 0's baseline was **3395 passed, 21 skipped, 3 deselected**. The +7
passed is accounted for exactly by this phase's own added tests (4 in
`test_frozen_bytecode_exclusion.py`'s parametrization, 1 in
`test_v5_alpha1_phase_e_starter_refresh.py`, 2 in
`test_windows_packaging_spec.py`'s new parametrized test) — **zero existing
test's expected result was changed, and zero new failures occurred.**

**`git diff --check`:** clean, exit `0` (three pre-existing CRLF-normalization
notices on files that already had CRLF line endings before this phase
touched them — an artifact of this Windows checkout's line-ending
configuration, not new whitespace/line-ending churn introduced by this
phase's edits).

---

## M. Files changed

| File | Change | Why |
|---|---|---|
| `app/services/engine.py` | Modified | Removed the dead `EngineRunner` class and every import that existed solely for it; added `__all__` to make the surviving `RunConfig`/`open_pygame_client_direct` re-export explicit (Section H). |
| `engine/tests/test_designer_third_entrant_command.py` | Modified | Updated one docstring sentence that described `build_engine_command`'s only caller as the now-removed `EngineRunner` (Section H). |
| `engine/tests/test_pmars.py` | Modified | Removed a comment referencing `EngineRunner` as a design parallel for the now-removed class (Section H). |
| `engine/src/battle_engine/starters.py` | Modified | FIND-04: case-fold the `__pycache__` directory check and add a loose `.pyc`/`.pyo` suffix filter in `starter_content_files` (Section D). |
| `engine/tests/test_v5_alpha1_phase_e_starter_refresh.py` | Modified | Added `test_digest_ignores_loose_bytecode_and_case_variant_cache_dirs` (Section D). |
| `tools/packaging_data.py` | Modified | FIND-07: case-fold the cache-directory-name comparison in `is_python_bytecode` (Section G). |
| `engine/tests/test_frozen_bytecode_exclusion.py` | Modified | Added two case-variant cache-directory paths to the existing `REJECTED_PATHS` parametrization (Section G). |
| `tools/agent_designer.spec` | Modified | FIND-06: bundle only `app/assets/branding` (at the same `"assets/branding"` destination) instead of the full repository-root `assets/` directory (Section F). |
| `tools/replay_viewer.spec` | Modified | FIND-06: same fix as `agent_designer.spec` (Section F). |
| `engine/tests/test_windows_packaging_spec.py` | Modified | Added `test_standalone_gui_specs_bundle_only_the_branding_icon` (Section F). |
| `tools/build_linux.sh` | Modified | FIND-05: added a post-build bytecode/cache debris check mirroring `build_win.ps1`'s (Section E). |
| `tools/installer.iss` | Modified | Removed the dead `replays` directory creation line from `[Dirs]`; documented why `logs` remains (Section I). |
| `tools/smoke_after_install.ps1` | Modified | Removed `"replays"` from the post-install writable-directory existence check to match (Section I). |
| `docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE2_TECHNICAL_HYGIENE.md` | Added | This report. |

No file was deleted. No file under `client/src`, `agents/` (tracked
fixtures), or any replay/agent/result data file was added, modified, or
deleted.

---

## N. Behavioral-neutrality conclusion

**No evidence exists that match behavior, ruleset semantics, replay
semantics, CLI/GUI behavior, or any Alpha-feedback-visible surface changed
as a result of this phase.** Specifically:

- The full regression suite passed with the exact same failure count (zero)
  as Phase 0's baseline, with the only count difference being this phase's
  own newly-added, explicitly-accounted-for tests.
- The strongest available determinism/equivalence suites
  (`-k "v5 or ruleset"`, `test_v4_stable_ruleset_equivalence.py`) passed with
  no new failures.
- Every pinned starter digest (`CURRENT_STARTER_DIGESTS`) is unchanged —
  the FIND-04 fix is proven, not merely argued, to be byte-identical for
  every currently-shipped starter.
- The FIND-06 fix preserves the exact frozen destination path
  (`assets/branding/bytefray-icon.png`) the runtime icon loader checks
  first; no icon-resolution behavior changed.
- No `engine/src/battle_engine` simulation/scheduler/scoring/termination/
  Agent-API module, no `client/src/battle_client` replay module, and no
  CLI/Designer argument, default, or workflow was touched at all.
- `bytefray --version` and a full headless Designer GUI startup both
  produced identical, error-free output to the pre-phase baseline.

---

## O. Recommended Phase 3 inputs

- **FIND-03** (starter-refresh atomicity) — a dedicated future phase, scoped
  explicitly as a *behavior-changing bug fix* (not hygiene), with
  interruption-simulation test infrastructure built first and cross-platform
  directory-replace semantics (Windows and POSIX) designed and reviewed
  before any implementation, per Section C/K.
- **Installer `logs/` directory** — relocate `smoke_after_install.ps1`'s
  diagnostic `installed-files.txt` write to a location that does not depend
  on the installer creating a otherwise-unused-by-the-product `logs/`
  directory, then re-evaluate whether `logs/` itself can also be dropped
  from `[Dirs]`, per Section I/K.
- **A full installer build+install+uninstall qualification pass** — to
  supply the release-lifecycle evidence this phase's `replays` removal
  documented but could not itself produce (Section I), and to fold in
  FIND-05's Linux debris check against a real build once Linux binary
  packaging is next exercised.
- **`build_engine_command`'s further removability** — now that its only
  production caller (`EngineRunner`) is gone, decide (separately from this
  phase) whether it should be removed from `engine_commands.py` entirely or
  is worth retaining as a directly-tested, GUI-independent command-builder
  utility, per Section K.
- Everything already carried forward from the Post-Release Hardening
  Audit's Section J "Suggested backlog" beyond FIND-03–07 (FIND-01/FIND-02
  were already remediated pre-Phase-0 by `e67787e`) remains the authoritative
  backlog for any future release-surface/ruleset/artifact audit; this report
  does not duplicate or supersede it.
