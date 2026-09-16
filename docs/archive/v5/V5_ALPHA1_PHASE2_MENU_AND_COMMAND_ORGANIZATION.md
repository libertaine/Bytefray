# Bytefray V5 Alpha 1 — Phase 2: Menu and Command Organization

Date: 2026-09-12. Branch: `v5-research`.
Starting HEAD: `45880b8f62f86dd28987a53bd4697b7ca60df49f` (clean working tree at start).
Final HEAD: unchanged (no commit per instruction); working tree carries the changes uncommitted.

Scope: Reorganize Bytefray Designer's menu hierarchy according to conventional desktop application expectations while strictly preserving all existing command behaviors, simulation rules, agent package formats, replay persistence, and tournament architectures.

---

## 1. Baseline and Initial Menu Inventory

Before modifying code, an audit of `app/agent_designer.py` and the full repository was conducted.

### 1.1 Initial Menu Structure
Prior to this phase, `AgentDesigner` constructed only two top-level menus in `_build_menus()`:

```text
Tools
  ├── Run Tournament…
  ├── Evaluation History…
  ├── Replay History…
  ├── [Separator]
  ├── Import Agent Package…
  ├── Inspect Agent Package…
  ├── [Separator]
  └── Open Last Output Folder

Help
  └── About Bytefray
```

### 1.2 Inventory of Existing Actions

1. **Run Tournament…**
   - Parent: `Tools` QMenu
   - Callback/Slot: `self._on_tournament`
   - Shortcut: None
   - Tooltip / Status tip: None
   - Other exposure: CLI command `bytefray tournament`
   - Dependencies: `tests/test_agent_designer_tournament.py` exercises `_on_tournament`.

2. **Evaluation History…**
   - Parent: `Tools` QMenu
   - Callback/Slot: `self._on_evaluation_history`
   - Shortcut: None
   - Tooltip / Status tip: None
   - Other exposure: Evaluation dialog ("History" button)
   - Dependencies: `tests/test_v5_replay_history_browser.py::test_designer_tools_menu_has_replay_history` asserts `"Evaluation History…" in labels` under `Tools`.

3. **Replay History…**
   - Parent: `Tools` QMenu
   - Callback/Slot: `self._on_replay_history`
   - Shortcut: None
   - Tooltip / Status tip: None
   - Other exposure: None within Designer UI
   - Dependencies: `tests/test_v5_replay_history_browser.py` explicitly checks `Tools` menu for `"Replay History…"`.

4. **Import Agent Package…**
   - Parent: `Tools` QMenu
   - Callback/Slot: `self._on_import_agent_package`
   - Shortcut: None
   - Tooltip / Status tip: None
   - Other exposure: CLI command `bytefray agent import`
   - Dependencies: `tests/test_agent_package_dialogs.py` exercises `_on_import_agent_package`.

5. **Inspect Agent Package…**
   - Parent: `Tools` QMenu
   - Callback/Slot: `self._on_inspect_agent_package`
   - Shortcut: None
   - Tooltip / Status tip: None
   - Other exposure: CLI command `bytefray agent inspect`
   - Dependencies: `tests/test_agent_package_dialogs.py` exercises `_on_inspect_agent_package`.

6. **Open Last Output Folder**
   - Parent: `Tools` QMenu (stored as `self.openOutputFolderAction`)
   - Callback/Slot: `self._on_open_output_folder`
   - Shortcut: None
   - Tooltip: Explanatory fallback priority tooltip added in Phase 1 (`"Opens this session's tournament output folder..."`)
   - Other exposure: None (Agent Development panel has separate "Open Agent Folder" for agent definitions)
   - Dependencies: `tests/test_v5_alpha1_phase1_corrective_cleanup.py::test_open_last_output_folder_tooltip_matches_actual_fallback_behavior` asserts tooltip content and `parent().toolTipsVisible()`.

7. **About Bytefray**
   - Parent: `Help` QMenu
   - Callback/Slot: `self._on_about`
   - Shortcut: None
   - Tooltip / Status tip: None
   - Other exposure: CLI `--version` / info
   - Dependencies: Standard metadata dialog.

---

## 2. Reorganized Menu Structure

The menu hierarchy was reorganized to follow desktop UI conventions:

```text
File
  ├── Import Agent Package…
  ├── Inspect Agent Package…
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

### 2.1 File Menu Additions & Relocations
- **File Menu Creation**: Created top-level `File` menu via `self.menuBar().addMenu("File")`. Enabled tooltips via `file_menu.setToolTipsVisible(True)` so that `Open Last Output Folder`'s hover documentation remains discoverable.
- **Import Agent Package…**: Moved from `Tools` to `File`. Label maintains ellipsis (`…`) because it opens an interactive file selection dialog followed by inspection/import prompts.
- **Inspect Agent Package…**: Moved from `Tools` to `File`. Label maintains ellipsis (`…`) because it opens an interactive file selection dialog.
- **Open Last Output Folder**: Moved from `Tools` to `File`. Label has no ellipsis (immediate action). Stored as `self.openOutputFolderAction` to maintain full attribute compatibility. The explanatory tooltip from Phase 1 is retained verbatim; its internal reference `(Tools > Run Tournament…)` remains completely accurate.
- **Exit**: Added explicit `Exit` command to `File`.
  - Slot: `self.close`
  - Shutdown path: Invokes `QMainWindow.close()`, which delivers a `QCloseEvent` to `AgentDesigner.closeEvent()`. This calls `self._dispose_process()` to terminate active runner processes, cleanly shuts down the replay history worker thread (`history.shutdownWorker()`), and passes to `super().closeEvent(event)`.
  - Shortcut: Configured with standard Qt platform key sequence `QKeySequence(QKeySequence.StandardKey.Quit)`.
  - Stored on `self.exitAction` for programmatic inspection.

### 2.2 Tools Menu Cleanup
- File-oriented actions were removed from `Tools`, eliminating duplication.
- Operational commands were preserved:
  - `Run Tournament…`
  - `Evaluation History…`
  - `Replay History…`
- Unneeded separators were removed, leaving a coherent cluster of analysis and execution tools.

### 2.3 Replay Browser Treatment
- Preserved under `Tools` as `Replay History…`. Per the task specification, no speculative relocation or architectural rework was undertaken. Existing tests asserting its presence under `Tools` continue to pass without alteration.

### 2.4 View and Help Menu Assessment
- **View Menu**: Audited all Designer panels and widgets. No genuine view, layout, scale, or theme toggles exist in Bytefray Designer. In accordance with Section 4 instructions ("do not create empty or artificial menus merely to satisfy that shape"), the `View` menu was deferred.
- **Help Menu**: Audited help/documentation commands. `About Bytefray` is already implemented and directly belongs under `Help`. The `Help` menu was preserved with `About Bytefray`.

### 2.5 Export Agent Package Deferral
- Per Section 5, `Export Agent Package` is deferred to Phase 3 (Agent Package Workflow). No disabled placeholder or incomplete exporter was added to `File`.

---

## 3. Keyboard Accessibility and Usability

- **Top-Level Menus**: `File`, `Tools`, `Help` are accessible via standard Qt menu bar focus mechanisms (`Alt` / `F10`) without custom event filters.
- **Menu Traversal**: Left/Right arrows navigate across menus; Up/Down arrows traverse actions; Enter activates selected commands; Esc dismisses menus.
- **Shortcuts & Mnemonics**: No shortcut collisions exist. Standard Qt Quit key sequence is associated with `Exit`, with `MenuRole.QuitRole` explicitly assigned. `About Bytefray` is assigned `MenuRole.AboutRole`.
- **Keyboard Reachability**: Tested keyboard activation without mouse events, confirming action invocation enters canonical window shutdown.
- **Tooltip Discoverability**: `file_menu.setToolTipsVisible(True)` ensures the detailed fallback chain documentation on `Open Last Output Folder` appears on hover.

---

## 4. Files Changed

1. `app/agent_designer.py`:
   - Imported `QAction` and `QKeySequence` from `PySide6.QtGui`.
   - Updated `_build_menus()` to construct `File`, `Tools`, and `Help` menus with correct action ownership, separators, tooltips, `Exit` binding to `self.close`, and standard `menuRole` assignments (`QuitRole` and `AboutRole`).
2. `tests/test_v5_alpha1_phase2_menu_organization.py`:
   - Comprehensive GUI regression test suite with 13 tests covering menu order, File contents, Tools cleanup, Help contents, canonical slot invocation wiring, Exit shutdown mechanics (including active subprocess disposal and replay history background worker shutdown), menu role verification, keyboard accessibility, shortcut collision checks, and offscreen GUI smoke.

---

## 5. Verification Record

### 5.1 Focused Tests
- `tests/test_v5_alpha1_phase2_menu_organization.py` — **13 passed** in 2.56s.
- `tests/test_v5_alpha1_phase1_corrective_cleanup.py` — **5 passed** in 0.83s.
- `tests/test_v5_replay_history_browser.py` (menu assertions) — **2 passed** in 0.67s.
- `tests/test_agent_package_dialogs.py` & `test_agent_evaluation_history_dialog.py` — **52 passed** in 5.44s.
- `tests/test_agent_designer_lifecycle.py` & `test_agent_designer_presentation.py` — **27 passed** in 4.09s.

### 5.2 Full GUI Suite
- Command: `python -m pytest tests/ client/tests/ -m gui`
- Result: **459 passed, 512 deselected**, 0 failed in 144.25s.

### 5.3 Canonical Headless Suite
- Command: `python -m pytest`
- Result: **3620 passed, 21 skipped, 3 deselected** (1 transient concurrent-pytest file conflict on `test_completion_order_reversal_preserves_matrix_order` isolated re-ran immediately: **1 passed** in 55.40s).

### 5.4 Lint
- Command: `python -m ruff check .`
- Result: **All checks passed!**

### 5.5 Type-Check
- `python -m mypy engine/src/battle_engine` — **Success: no issues found in 113 source files**.
- `python -m mypy client/src/battle_client` — **Success: no issues found in 16 source files**.

### 5.6 Manual / Offscreen GUI Validation
- Tested via offscreen Qt (`QT_QPA_PLATFORM=offscreen`) verifying widget instantiation, menu bar construction, action triggering, tooltip visibility, subprocess cleanup, worker shutdown, and clean window closing.
- True sighted interactive pixel review was not possible in this headless/remote environment.
