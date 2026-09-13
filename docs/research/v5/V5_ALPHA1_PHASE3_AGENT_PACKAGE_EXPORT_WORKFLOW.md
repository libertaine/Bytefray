# Bytefray V5 Alpha 1 — Phase 3: Agent Package Export Workflow

Date: 2026-09-12. Branch: `v5-research`.
Starting HEAD: `4f7fc10c8390bec67592df27673b8b71e57688c8` (clean working tree at start).
Final HEAD: unchanged (no commit per instructions; working tree carries changes).

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
   - Updated `test_file_menu_actions_and_ordering` and `test_designer_gui_menu_smoke_offscreen` to accept the 7-action Phase 3 layout while maintaining full validation for the 6-action Phase 2 baseline.
3. `tests/test_v5_alpha1_phase3_export_package.py`:
   - Dedicated regression suite with 14 tests covering menu integration, action wiring, selection guards, unexportable agent handling, file dialog saving, extension normalization, overwrite confirmation (prompt, decline, and accept), cancellation, error handling, unexpected exceptions, round-trip export/inspect/import, and source immutability.
4. `docs/specs/agent_package.md`:
   - Documented `File → Export Agent Package…` integration in Section 13.
