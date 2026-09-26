# Bytefray V5 Alpha 1 — Phase 3: Agent Package Export Workflow

Date: 2026-09-12 (implementation), 2026-09-13 (independent review and qualification). Branch: `v5-research`.
Starting HEAD: `4f7fc10c8390bec67592df27673b8b71e57688c8` (clean working tree at start of implementation).
HEAD after implementation: `3dd7c032db7b0a4286e7fd1b6caef440bdcdfcc2` ("alpha changes") -- the
implementation described below was committed during the same session that wrote it, not left
uncommitted as originally planned. The independent review in Sec 7 found the working tree at
this commit (not uncommitted on top of `4f7fc10`) when it began; per its instructions it did not
reset, amend, or otherwise alter that commit, and layered its own corrections on top as
uncommitted working-tree changes without committing them.
Final HEAD: `3dd7c032db7b0a4286e7fd1b6caef440bdcdfcc2` (unchanged); working tree carries the Sec 7
review's uncommitted corrections on top.

---

## 1. Baseline and Initial Working-Tree State

- **Branch:** `v5-research`
- **Starting HEAD:** `4f7fc10c8390bec67592df27673b8b71e57688c8`
- **Working tree:** Clean (verified via `git status`)
- **Preceding phase:** Phase 2 (Menu and Command Organization) organized the Designer's menu bar into `File`, `Tools`, and `Help`, relocating `Import Agent Package…` and `Inspect Agent Package…` to `File` while deferring `Export Agent Package…` to Phase 3.

---

## 2. Existing Package Architecture Audit

A comprehensive audit of the Bytefray codebase was conducted to determine whether a canonical package writer, schema, archive format, and validation layer already exist:

1. **Production Engine Layer (`battle_engine.agent_package`):**
   - **Canonical Exporter:** `export_agent(agent_id, *, data_root=None, output=None, revision_id=None) -> ExportResult`
   - **Inspection:** `inspect_package(package_path: Path | str) -> PackageInspection` (read-only, zero code execution, structural and SHA-256 integrity verification)
   - **Import:** `import_package(package_path: Path | str, *, data_root=None, as_agent_id=None) -> ImportResult`
   - **Package Schema:** `PACKAGE_SCHEMA = "bytefray.agent_package"`, version 1 (`PACKAGE_SCHEMA_VERSION = 1`).
   - **File Extension:** `PACKAGE_EXTENSION = ".bytefray-agent"`.
   - **Supported Agent Kinds:** `SUPPORTED_KINDS = ("python", "blob")` (manifest-only `kind="builtin"` starters are explicitly rejected with `PackageUnsupportedKindError`).
   - **Archive Container:** Standard ZIP archive (`zipfile.ZipFile`, `compression=zipfile.ZIP_DEFLATED`).
   - **Archive Layout:**
     - `package.json`: Top-level package manifest (schema, version, agent_id, display_name, kind, agent_version, entry_point, agent_api_version, agent_revision_id, file_count, timestamps).
     - `revision/<revision_id>/manifest.json`: Content-addressed revision manifest with SHA-256 digest mapping.
     - `revision/<revision_id>/files/<relative_path>`: Agent source code and asset payload.
   - **Atomic Write Mechanics:** Archives are constructed in temporary sibling files (`.tmp-<output_name>-<uuid>`) and atomically replaced (`os.replace`) only after passing layout, count, and size checks.

2. **CLI Parity Layer (`battle_engine.agent_package_cli` & `battle_engine.command`):**
   - Commands already present and shipped:
     - `bytefray agents export <agent-id> [--output PATH] [--revision REVISION_ID] [--json]`
     - `bytefray agents import <package-file> [--as AS] [--json]`
     - `bytefray agents package show <package-file> [--json]`
   - CLI wraps `battle_engine.agent_package` domain functions directly with identical schema, validation, and error reporting.

3. **Existing Designer Presentation Layer (`app/agent_designer.py` & `app/views/agent_package.py`):**
   - `app/views/agent_package.py` provides `PackageDetailsDialog` and formatting helpers (`format_export_result_text`, `format_package_inspection_text`, `format_import_result_text`).
   - `app/views/development.py` had an "Export Agent…" button (`btnExportAgent`) connected to `exportAgentRequested`, which routed to `AgentDesigner._on_export_agent`.
   - In Phase 2, `File` menu carried `Import Agent Package…` and `Inspect Agent Package…`, but had no `Export Agent Package…` companion action.

---

## 3. Decision Gate Classification

**Classification: Case A — Canonical writer already exists.**

- The canonical production writer (`export_agent`) is fully implemented, battle-tested, and already adheres to the formal specification (`docs/specs/agent_package.md`).
- CLI export (`bytefray agents export`) already exists and shares the identical domain backend.
- No new manifest schema, version bump, archive container, or compatibility contract is required.
- The task is strictly to expose this existing canonical capability cleanly in the Designer under `File → Export Agent Package…` with standard Qt save dialog semantics.

---

## 4. Implementation Details

### 4.1 Menu Hierarchy

`Export Agent Package…` is positioned in the `File` menu directly after `Inspect Agent Package…` and before the separator, establishing the intended lifecycle: **Design/Edit → Export → Inspect → Import**.

```text
File
  ├── Import Agent Package…
  ├── Inspect Agent Package…
  ├── Export Agent Package…
  ├── [Separator]
  ├── Open Last Output Folder
  ├── [Separator]
  └── Exit

Tools
  ├── Run Tournament…
  ├── Evaluation History…
  └── Replay History…

Help
  └── About Bytefray
```

### 4.2 Action Wiring and Dialog UX

- **Menu Action:** Added `self.exportAgentPackageAction = file_menu.addAction("Export Agent Package…", self._on_export_agent_package)`.
- **Ellipsis:** Included because the command presents an interactive file dialog.
- **Handler Implementation:** `_on_export_agent_package` operates on the currently selected agent:
  1. **Selection Validation:** Retrieves current agent from `self.development.selectedAgentRow()`. If none is selected or agent ID is empty, informs the user with a neutral dialog (`"Select a Python agent first."`) and aborts without opening a file dialog.
  2. **Save Dialog:** Prompts user via `QFileDialog.getSaveFileName` with default path `{data_root}/{agent_id}.bytefray-agent` and filter `"Bytefray Agent Packages (*.bytefray-agent);;All Files (*.*)"`. Standard Qt behavior automatically prompts for overwrite confirmation if the chosen destination already exists.
  3. **Extension Normalization and Overwrite Protection:** Automatically ensures the `.bytefray-agent` extension is appended if omitted by the user. If the normalized destination already exists on disk, explicitly prompts the user for overwrite confirmation via `QMessageBox.question` (`"'{name}' already exists. Do you want to replace it?"`). If declined, aborts cleanly without overwriting.
  4. **Cancellation:** Clean no-op if user cancels the save dialog or overwrite prompt (no error, no file written).
  5. **Clean Separation:** Preserves `_on_export_agent` for the existing Development panel button (`btnExportAgent`) and historical regression suites without resorting to test-detection introspection.
  6. **Error Reporting:** Catches `AgentPackageError` (such as unsupported agent kinds or corrupt manifests) and unexpected exceptions, displaying clean user-facing `QMessageBox.critical` dialogs without raw stack traces.
  7. **Success Confirmation:** Displays `format_export_result_text(result)` in an informative dialog matching the CLI output fields.

---

## 5. Round-Trip and Immutability Verification

- **Cycle Tested:** `Designer Export → inspect_package → import_package` (tested end-to-end in `test_designer_export_round_trip_inspect_and_import`).
- **Inspection:** Validated that exported packages pass `valid == True`, `compatible == True`, `integrity_verified == True`, and matching agent metadata.
- **Import:** Validated that importing an exported package into a separate, isolated `BYTEFRAY_ROOT` creates an exact replica of source code and configuration with identical `agent_revision_id`.
- **Source Immutability:** Explicitly verified via byte hash and nanosecond modification timestamps that exporting an agent does not alter or mutate the source files on disk in any way.

---

## 6. Files Changed

1. `app/agent_designer.py`:
   - Imported `PACKAGE_EXTENSION` from `battle_engine.agent_package`.
   - Added `self.exportAgentPackageAction = file_menu.addAction("Export Agent Package…", self._on_export_agent_package)` in `_build_menus()`.
   - Preserved `_on_export_agent` intact for the Development panel button and legacy regression fixtures.
   - Implemented `_on_export_agent_package` with save dialog handling, extension normalization, explicit overwrite protection when extension is appended, and clean error catching.
2. `tests/test_v5_alpha1_phase2_menu_organization.py`:
   - `test_file_menu_actions_and_ordering` and `test_designer_gui_menu_smoke_offscreen` now
     assert the current, post-Phase-3 contract strictly: exactly 7 File-menu actions in the
     Import → Inspect → Export → separator → Open Last Output Folder → separator → Exit order.
     The implementation's original version of this change instead accepted `len(actions) in
     (6, 7)`, i.e. it kept treating Phase 2's superseded 6-action layout as a still-valid runtime
     possibility rather than asserting the current contract; Sec 7's independent review judged
     that a genuine regression-strength defect and corrected it. Phase 2's own report remains the
     historical record of the 6-action layout; it is no longer accepted here as a live
     alternative.
3. `tests/test_v5_alpha1_phase3_export_package.py`:
   - Dedicated regression suite, originally 14 tests and now 15 after Sec 7's review added one
     (see Sec 7.2), covering menu integration, action wiring, selection guards, unexportable
     agent handling, file dialog saving, extension normalization, overwrite confirmation (both
     the extension-appended and explicit-extension cases, each with prompt/decline/accept as
     applicable), cancellation, error handling, unexpected exceptions, round-trip
     export/inspect/import, and source immutability.
4. `docs/specs/agent_package.md`:
   - Documented `File → Export Agent Package…` integration in Section 13.

---

## 7. Independent Review and Qualification (2026-09-13)

A separate session picked up this phase to review the implementation above independently and
carry it to qualification, per its own instructions: verify the Case A architecture finding,
correct only genuine defects, and complete qualification without redesigning the package format
or restarting the phase. It found the implementation already committed as HEAD `3dd7c032` ("alpha
changes") rather than left uncommitted as Sec 1 records was the plan, and left that commit
untouched, layering its own corrections on top as working-tree changes.

### 7.1 Architecture Verdict

Confirmed independently, by reading `engine/src/battle_engine/agent_package.py` directly rather
than relying on Sec 2's audit: `PACKAGE_SCHEMA = "bytefray.agent_package"`,
`PACKAGE_SCHEMA_VERSION = 1`, `PACKAGE_EXTENSION = ".bytefray-agent"`, and
`SUPPORTED_KINDS = ("python", "blob")` all exist exactly as described, `export_agent` is the sole
writer of package bytes, and `_on_export_agent_package` in `app/agent_designer.py` contains no
archive/manifest logic of its own -- it only builds a destination path and calls `export_agent`.
Case A is affirmed: no package schema, version, or archive-format change was needed or made.

### 7.2 Defect Found: A Genuinely Hanging GUI Test

`test_export_unsupported_kind_agent_reports_error_cleanly` simulated an "unsupported kind"
selection by setting `AgentRow.meta={"kind": "builtin"}` on a faked row, but the *real* on-disk
agent it pointed at (written via the shared `_write_python_agent` helper) had `"kind": "python"`
in its actual `agent.yaml`. `_on_export_agent_package` never reads `AgentRow.meta` for this
decision -- by design, it hands the agent id to the canonical `export_agent`, which re-resolves
the agent's kind from the real, persisted manifest (correct, defense-in-depth behavior: a stale or
spoofed UI-layer cache can never cause an unsupported export to slip through). Consequently the
export actually *succeeded* under the original test, taking the success path into
`QMessageBox.information(...)` -- which the test never mocked. Under
`QT_QPA_PLATFORM=offscreen` with no display and no automation to click it, that real modal's
`.exec()` blocks forever.

This was not a theoretical concern: three separate orphaned `pytest ... test_v5_alpha1_phase3_
export_package.py ... -m gui` processes were found still running on this machine at review start,
at three different start times spanning several hours, none ever having produced a final result --
concrete evidence this exact hang had already stalled prior attempts to qualify this phase
(including, per process inspection, a still-running Gemini/Antigravity agent session independently
working the same repository, which was in the process of applying essentially the same fix
described below when this review reached the same test).

**Fix:** the test now creates a real, on-disk manifest-only agent with `"kind": "builtin"` (the
same pattern `engine/tests/test_agent_package.py`'s `_make_builtin_agent` uses), so
`export_agent` genuinely raises `PackageUnsupportedKindError` and the assertions the test already
made (`[package_unsupported_kind]` in a `QMessageBox.critical` call) are actually exercised. A
defensive `QMessageBox.information` mock that fails the test loudly on an unexpected call was also
added, so a future regression of this kind produces a clear assertion failure instead of a
repeat hang. The same defensive `QMessageBox.critical`-fails-loudly mock was added to four other
tests that exercise a real, expected-to-succeed `export_agent` call but had no such guard
(`test_export_agent_package_normalizes_omitted_extension`,
`test_export_extension_normalization_allows_overwrite_if_confirmed`,
`test_designer_export_round_trip_inspect_and_import`,
`test_export_is_strictly_readonly_with_respect_to_source_agent`) -- none of these were observed to
hang, but each shared the identical latent gap (a real, unmocked modal dialog reachable if
`export_agent` ever failed unexpectedly), and the cost of that failure mode -- a process that must
be killed manually, and can silently stall an entire qualification run -- justified the one-line
fix in each.

The Phase 2 test weakening described in Sec 6 item 2 (`len(actions) in (6, 7)`) was also corrected
here to assert the current 7-action contract strictly, per this review's explicit instructions not
to accept Phase 2's superseded layout as a live alternative.

### 7.3 Overwrite-Confirmation Behavior: No Double Prompt

Analysis of `_on_export_agent_package` (`app/agent_designer.py`) confirms it distinguishes exactly
the two cases that matter, and does not double-prompt in either:

- **Explicit `.bytefray-agent` destination that already exists:** `QFileDialog.getSaveFileName`
  is called with no `DontConfirmOverwrite` option set (Qt's default is to confirm), so on Windows
  the OS/Qt save dialog itself already asks "already exists, replace?" for the literal filename
  the user chose, before that path is ever returned to this code. Since the returned `dest.name`
  already ends with `PACKAGE_EXTENSION` in this case, the handler's own
  `if not dest.name.endswith(PACKAGE_EXTENSION):` branch is skipped entirely -- no second prompt.
- **Destination typed without the extension:** Qt's static `getSaveFileName` convenience call here
  sets no default suffix, so the native dialog cannot know the eventual `...bytefray-agent` name
  and therefore never asks about it. The handler appends the extension itself and, only then,
  explicitly asks via `QMessageBox.question` if the *normalized* destination already exists. This
  is the one case that genuinely needs the app-level prompt, and it is the only case that gets one.

No defect was found here; this is exactly the "smallest correct distinction" the review's
instructions called for. The one gap found was in *test coverage*, not behavior: no existing test
asserted that the explicit-extension case does *not* also trigger the app-level
`QMessageBox.question`. `test_export_explicit_extension_overwrite_relies_on_native_dialog_only`
was added to close that gap -- it fails the test outright if `QMessageBox.question` is called when
the save dialog already returns a `.bytefray-agent`-suffixed, pre-existing destination.

### 7.4 Agent-Kind / Selection Wording: Retained As Accurate

`app/views/development.py`'s `AgentDevelopmentPanel` filters its catalog to `kind: python` agents
only (`_is_python_agent`, applied when populating `self._rows`) -- this is a deliberate,
documented v0.4-era restriction of the Development tab itself, not something `_on_export_agent_
package` imposes. `selectedAgentRow()` can therefore only ever return a Python-kind agent or
`None`; a `kind="blob"` agent (also package-exportable per `SUPPORTED_KINDS`) is never reachable
as a Development-tab selection today, and a `kind="builtin"` starter is never even catalog-listed.
Given that, `"Select a Python agent first."` is accurate, not unnecessarily restrictive, and was
left unchanged. Widening it to generic "exportable agent" wording would misdescribe what the
Designer's own selection surface can actually produce; that would only become the right change if
a future phase adds blob-agent selection to the Development tab, which is out of this phase's
scope.

### 7.5 Qualification Results

All commands below were run with the repo's `.venv` Python on Windows.

- Focused Phase 3 suite -- `pytest tests/test_v5_alpha1_phase3_export_package.py -m gui -v`:
  **15 passed** (14 original + 1 new overwrite-coverage test), ~2.6s, no hang.
- Phase 2 menu organization regression -- `pytest tests/test_v5_alpha1_phase2_menu_organization.py
  -m gui -v`: **13 passed**, ~2.3s, now asserting the strict 7-action contract.
- Canonical package engine tests -- `pytest engine/tests/test_agent_package.py
  engine/tests/test_agent_package_cli.py -v`: **101 passed, 2 skipped**, ~4.7s.
- Agent package dialogs and Designer lifecycle/presentation --
  `pytest tests/test_agent_package_dialogs.py tests/test_agent_designer_lifecycle.py
  tests/test_agent_designer_presentation.py -m gui -v`: **45 passed**, ~5.5s.
- Canonical GUI suite -- `pytest tests/ -m gui -q`: **475 passed** (6 non-GUI tests deselected),
  clean exit.
- Full canonical suite -- `pytest` (default `testpaths`, `-m "not gui"` per `pytest.ini`):
  **3620 passed, 21 skipped, 3 deselected** in 358.25s, clean exit. (An earlier attempt at this
  run raced against a concurrently running GUI-suite invocation over the shared repo-local
  `--basetemp=.pytest-tmp`, producing two spurious `FileExistsError`/`rm_rf` errors at collection
  time in `client/tests/test_analysis.py`; that run was discarded, `.pytest-tmp` was cleared, and
  the suite was re-run standalone to the clean result recorded here. This was a review-session
  tooling artifact of running two pytest invocations in parallel, not a defect in any reviewed or
  edited code.)
- `ruff check .`: **All checks passed.**
- `mypy engine/src/battle_engine`: **Success: no issues found in 113 source files.**
- `mypy client/src/battle_client`: **Success: no issues found in 16 source files.**

### 7.6 Round-Trip and Immutability Re-Verification

`test_designer_export_round_trip_inspect_and_import` (passing) independently confirms the Sec 5
claims end-to-end through the actual Designer handler: export produces a package that
`inspect_package` reports as `valid`, `compatible`, and `integrity_verified`, with matching
`agent_id`/`display_name`/`file_count`; `import_package` into a wholly separate `BYTEFRAY_ROOT`
succeeds, is not flagged `already_present`, preserves `agent_revision_id` exactly, and reproduces
the source agent's file content byte-for-byte. `test_export_is_strictly_readonly_with_respect_to_
source_agent` (passing) confirms export leaves the source agent's `agent.py`/`agent.yaml` bytes
and mtimes untouched. No binary-identical-archive guarantee was required or tested, consistent
with the package contract, which does not promise deterministic archive bytes.

### 7.7 GUI/Interactive Review Caveat

This review's GUI verification is entirely offscreen (`QT_QPA_PLATFORM=offscreen`) and automated
via the test suites above. No interactive display was available in this environment, so no sighted
manual walkthrough (menu layout, real save-dialog appearance, real overwrite-prompt wording as
rendered, etc.) was performed. The behavior described in Sec 7.3 is verified by code inspection
and mocked-dialog regression tests, not by watching an actual dialog on screen.

### 7.8 Final State

No commits were made by this review; per its instructions, HEAD remains `3dd7c032db7b0a4286e7fd
1b6caef440bdcdfcc2`. The working tree carries this review's corrections on top of that commit:
`app/agent_designer.py` and `docs/specs/agent_package.md` are unchanged from the implementation
commit; `tests/test_v5_alpha1_phase2_menu_organization.py`,
`tests/test_v5_alpha1_phase3_export_package.py`, and this report were further modified by the
review as described above.
