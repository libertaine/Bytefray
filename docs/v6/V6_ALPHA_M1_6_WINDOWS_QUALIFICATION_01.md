# Bytefray V6 — M1-6A Windows Qualification Report 01

2026-10-11, America/Indianapolis.

**M1-6A WINDOWS — FORMALLY CLOSED**\
**Qualification disposition: PASS**\
**Linux M1-6B: NOT STARTED**\
**Overall M1 Alpha 1 acceptance: PENDING LINUX**

This report documents the Windows AMD64 qualification portion of **M1-6: Final Alpha 1 Acceptance and Platform Qualification**, executed pursuant to Project Lead authorization under [V6 Alpha M1 Contract 01](V6_ALPHA_M1_CONTRACT_01.md), [Phase 0 Decision Packet 01](V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md), and closed M1-1 through M1-5 milestones.

Project Lead accepted Windows functional qualification. The final inventory audit
reconciled the earlier 4,124 estimate to the retained 3,218-case product selection
and identified required compatibility cases embedded in excluded modules. Those
328 cases now pass in a separate supplemental run. The original broad result
remains 3,199 passed, 19 skipped, 7 GUI deselected, zero failures/errors; it was
not rerun or combined with overlapping focused selections. A separate closure
GUI run passed all seven GUI-selected client cases. AC1–AC11 are PASS within the
authorized Windows M1 scope. No blocking defects remain. Formal Windows closure
does not grant overall M1 acceptance or authority to begin Linux M1-6B.

Exact inventories and privacy-filtered JUnit records are retained in
[the closure evidence packet](evidence/m1_6a_windows/README.md). Original logs,
XML, screenshots and the pre-closure report remain locally preserved.

---

## 1. Exact Baseline and Environment

### 1.1 Repository Parity and Working Tree

- **Repository Root:** repository checkout (local path omitted)
- **Branch:** `v6-research`
- **Starting HEAD Commit:** `ab35b5c35056ad6dbbec4db895017399daaaa998`
- **Remote:** `https://github.com/libertaine/Bytefray.git`
- **Local Upstream Ref:** `origin/v6-research` matches local HEAD at `ab35b5c35056ad6dbbec4db895017399daaaa998`.
- **Starting Tracked Working Tree:** Clean; starting index empty. Final staged contents are qualification-only (Section 13).
- **Diff Whitespace & Formatting:** `git diff --check` and `git diff --cached --check` returned 0 warnings/errors.
- **Untracked Inventory:** All inherited private E9 study materials, disposition records, and seal declarations remain preserved untouched.

### 1.2 Platform & Toolchain Environment

```text
Operating System: Windows 11 Pro Build 10.0.26120 (Windows-11-10.0.26120-SP0)
Architecture: AMD64 (64-bit)
Python Interpreter: Python 3.13.14 (tags/v3.13.14:fd17997, Jun 10 2026, 13:03:48) [MSC v.1944 64 bit (AMD64)]
Virtual Environment: repo-local .venv
PySide6 / Qt Version: PySide6 6.11.2 / Qt 6.11.2
Pygame / SDL Version: pygame-ce 2.5.8 / SDL 2.32.10
Qt QPA Platform: windows
SDL Video Driver: windows
Display Resolution: 2048 x 1152, 32-bit RGB888
```

---

## 2. Windows Acceptance Matrix (AC1–AC11)

| Criterion | Contract Requirement | Existing Qualified Evidence | New Windows Verification | Actual Test or Native Interaction | Result & Evidence Path | Status |
|---|---|---|---|---|---|---|
| **AC1: Legality** | Target normalization, circle reach boundary, ±27 window; out-of-reach consumes 1 action and yields null/false; invalid kind/operand forfeits; stable v4 refuses SENSE. | M1-1 policy tests, M1-3 playback validator. | Native Windows subprocess dry-run and validation preflight. | `test_v6_alpha_m1_policy_capabilities.py`, `test_v6_alpha_m1_3_sensing_playback.py`, native Designer validate. | Status: Valid/Invalid reported before execution. [tools/qualification/run_native_designer_workflow.py](../../tools/qualification/run_native_designer_workflow.py), [docs/screenshots/v6_alpha1_windows/](../screenshots/v6_alpha1_windows/) | **PASS** |
| **AC2: Price** | SENSE, empty, and rejected scans each consume exactly 1 action; budget Q=8 permits no 9th action; no mutation, territory, movement or disruption from sensing. | M1-1 runtime tests, M1-3 budget reconciliation. | Windows controller counters & trace validation under native match service. | `test_ruleset_v6_alpha1_single_process_budget_exhaustion`, native match run. | 1 action consumed per SENSE, 0 world byte modifications. `test_v6_alpha_m1_policy_capabilities.py` | **PASS** |
| **AC3: Availability** | Passive visibility is empty; exact sorted unique enemy sample including disrupted live anchors, excluding own/dead anchors. | M1-1 active policy, M1-3 trace reconstruction. | Windows native execution with moving and stationary opponents. | `test_v6_alpha_m1_2_window_scout.py`, `test_v6_alpha_sensing.py`. | `visible_enemy_anchor_addresses=()`; SENSE samples exact anchors (91). | **PASS** |
| **AC4: Delivery** | Receipt arrives on next same-process callback in chunk/later tick; distinct empty/refused/absent; elimination/limit before next callback leaves no receipt. | M1-3 delivery validator, M1-4 phase cursor. | Full native trace delivery inspection on Windows. | `test_v6_alpha_m1_3_sensing_playback.py`, `tools/qualification/run_determinism_and_neg_cases.py`. | Callback 2 receives `previous_sense_anchors=(91,)`; [docs/screenshots/v6_alpha1_windows/C_delayed_receipt.png](../screenshots/v6_alpha1_windows/C_delayed_receipt.png) | **PASS** |
| **AC5: Knowledge** | No pre-receipt contacts; historical samples retain sample-time location after opponent moves; local empty scan does not clear other windows; no tooltips or pacing leakage. | M1-4 filtered perspective models, M1-5 adversarial. | Windows native GUI inspection, scene line and marker verification. | `client/tests/test_v6_alpha_sensing_adversarial.py`, `client/tests/test_v6_alpha_m1_5_adversarial.py`. | Opponent current position hidden; contact 91 retained with age; [docs/screenshots/v6_alpha1_windows/F_historical_knowledge.png](../screenshots/v6_alpha1_windows/F_historical_knowledge.png) | **PASS** |
| **AC6: Reconstruction** | Native match artifacts pass result association, raw trace digest, sample re-derivation, tick world agreement. Mismatch refuses verified playback. Replay-only fallback. | M1-3 sensing playback, M1-5 fallback. | Windows filesystem artifact pair validation, corrupt/missing trace negative tests. | `tools/qualification/run_determinism_and_neg_cases.py`, `test_v6_alpha_m1_3_sensing_playback.py`. | Corrupt/missing trace disables filtered view with clean notice; valid pair passes. | **PASS** |
| **AC7: Client Agreement** | Cursor exposes request, receipt, MOVE, WRITE in order; tick ends agree with ReplaySession; pause, step, rewind, view switch reproduce prefix without leakage. | M1-4 cursor tests, M1-5 renderer tests. | Windows native Pygame event loop and screen capture across phases. | `client/tests/test_v6_alpha_m1_5.py`, [tools/qualification/run_native_designer_workflow.py](../../tools/qualification/run_native_designer_workflow.py), [tools/qualification/run_native_viewer_control_witness.py](../../tools/qualification/run_native_viewer_control_witness.py). | Exact TICK_END agreement; 8 teaching frames (`A`–`H`) and 4 native control witness frames (`witness_control_01`–`04`) in [docs/screenshots/v6_alpha1_windows/](../screenshots/v6_alpha1_windows/). State transitions confirmed in-process and in live unmocked subprocess with verified pixel diffs (8,398 / 10,231 / 33,431). | **PASS** |
| **AC8: Reproduction** | Deterministic teaching inputs yield identical logical world records, ordered trace decisions, and terminal results across repeated runs. Complete capture & source fingerprint. | M1-2 demo runner determinism. | Repeated completed Windows native runs with seed 0, comparing replays, traces, and demo sidecars. | `tools/qualification/run_determinism_and_neg_cases.py`. 0 replay diffs, 0 trace logical diffs. | Replays identical (103 lines); 1600 trace records identical excluding wall_time_ms. | **PASS** |
| **AC9: Authoring** | Personal copy creation, parameter modification, preflight capability rejection, native execution, result association, and settings-change labeling. | M1-5 Designer tests. | Full 13-step native Windows Qt workflow with real subprocesses and native launcher. | [tools/qualification/run_native_designer_workflow.py](../../tools/qualification/run_native_designer_workflow.py), 7 native screenshots saved to `docs/screenshots/v6_alpha1_windows/`. | Bounded copy created, capability rejected on v4, validated on alpha1, runs 1 & 2 distinct. | **PASS** |
| **AC10: Compatibility** | Stable v4 fixtures, ruleset equivalence, runtime defaults, and historical readers remain intact. Retired execution refused. | M1-1 baseline disposition, stable v4 suite. | Windows regression run of all v4 immutability, equivalence, and catalog suites, plus complete broader product regression complement. | `test_v4_historical_immutability.py`, `test_v4_stable_ruleset_equivalence.py`, `work/m1_6a_windows_regression_final.xml`. | All 32 v4 tests pass; stable v4 remains untouched default ruleset. Broader Windows product regression complement PASSED (3,199 passed, 19 skipped, 7 deselected, 0 failures, 0 errors in 380.62s; JUnit XML `work/m1_6a_windows_regression_final.xml`). Combined with M1-1 frozen baseline (72/72 passing). | **PASS** |
| **AC11: Research Isolation** | Product implementation/demo routes make zero calls/imports of E8/E9 tools; no research seeds or authority events; product runs write to authorized locations; 329 frozen-baseline pins and 1,447 backup files preserved. | M1-1 through M1-5 preservation records. | Windows filesystem and cryptographic digest audit of pins and backups. | Read-only verification of preserved baseline `b948540` and local backup `M1-4_20261011_7d98e0a0`. | 329/329 preserved-baseline pins match; 1384 study files match; 1447/1447 backup files match. Current product source is a distinct committed instrument. | **PASS** |

---

## 3. Real Native Designer Authoring Workflow Evidence

The required 13-step end-to-end authoring workflow was executed using real native Windows Qt windows (`QT_QPA_PLATFORM=windows`) in an isolated temporary environment. Real child subprocesses and real Win32 message loop dispatching were employed. **The replay launcher was not mocked or intercepted.**


The retained automation groups the contract's 13 actions: (1) launch, (2)
stable default, (3) copy, (4) select alpha1, (5) configure parameters, (6)
validate, (7) reject v4 mismatch, (8) run match, (9) confirm recorded identity
and parameters, (10) open replay, (11) post controls, (12) close replay, (13)
edit/rerun and distinguish results. Mismatch was exercised before alpha1
selection; some actions share one automation block. The numbered narrative
below groups them into 12 entries and includes final Designer shutdown.
This is a programmatically driven native workflow, not 13 independent manual
interactions or 13 pytest cases. The later four-frame witness confirms forward
phase stepping and play/unpause; separate controller/SDL tests support other
controls. Original screenshots 06/07 retain private paths and remain local.

Execution log and artifact record from [tools/qualification/run_native_designer_workflow.py](../../tools/qualification/run_native_designer_workflow.py):

1. **Launch Normal Application:** `AgentDesigner` initialized under native QPA `windows`. Window displayed at native desktop resolution. Visible: `True`. Screenshot: [01_designer_launched.png](../screenshots/v6_alpha1_windows/01_designer_launched.png) (48,230 bytes).
2. **Confirm Stable v4 Default:**
   - Development tab: `designer.development.selected_ruleset_id() == 'bytefray-rules-4'`.
   - Advanced tab: `designer.advanced.ruleset.currentData() == 'bytefray-rules-4'`.
3. **Create Personal Copy of Window Scout:**
   - Navigated to `Agent Development` tab. Triggered `NewAgentDialog(designer.data_root)`. Selected template `window_scout`, named `my_window_scout`.
   - Result: `agents/my_window_scout/agent.py` and `agents/my_window_scout/agent.yaml` created.
   - Refreshed catalog and selected agent. Screenshot: [02_window_scout_copied.png](../screenshots/v6_alpha1_windows/02_window_scout_copied.png) (67,635 bytes).
4. **Confirm Capability Mismatch Rejection:**
   - Selected `my_window_scout` in Development under `bytefray-rules-4`.
   - Test button disabled (`isEnabled() == False`); explanation directs explicit alpha1 selection.
   - Clicked Validate (`btnValidate`): child process dry run exited with structured failure:
     `Stage: load; Code: agent_capability_unsupported; Error: Ruleset 'bytefray-rules-4' does not provide required capabilities: sense. Select an explicitly compatible Ruleset.`
   - Rejection occurred **before agent code execution or match artifact creation**. Screenshot: [03_capability_mismatch_rejected.png](../screenshots/v6_alpha1_windows/03_capability_mismatch_rejected.png) (62,561 bytes).
5. **Select bytefray-rules-6-alpha1 and Validate:**
   - Selected `bytefray-rules-6-alpha1` in `rulesetCombo`.
   - Test button became enabled. Clicked Validate: child process returned:
     `Last validation: Valid; API: 2; Dry-run action: SENSE operand=91`. Screenshot: [04_alpha1_validated.png](../screenshots/v6_alpha1_windows/04_alpha1_validated.png) (61,233 bytes).
6. **Configure Parameters in Advanced Tab:**
   - Switched to `Advanced` tab, `Agent Params` sub-tab (tab index 1).
   - Selected Ruleset `bytefray-rules-6-alpha1`, Agent A `my_window_scout`, Agent B `v4_scout`.
   - Configured: `search_interval = 2`, `move_step = 32`, `ticks = 5`.
   - Parameter constraints verified: max move step 64, schema validation errors: none. Screenshot: [05_advanced_parameters_configured.png](../screenshots/v6_alpha1_windows/05_advanced_parameters_configured.png) (45,131 bytes).
7. **Execute Complete Native Match:**
   - Switched to `Match Setup` sub-tab. Clicked Run (`btnRun`). Supervised child process ran `NativeMatchService`.
   - Switched to `Results` sub-tab.
   - Result ID: `result_228415a9fd518026efac41c4`.
   - Ruleset: `bytefray-rules-6-alpha1`.
   - Recorded parameters: `{"search_interval": 2, "move_step": 32}`.
   - Associated files: `replay.jsonl` and `trace.jsonl` present and verified. Screenshot: `06_match_completed.png` (local-only original; hash in evidence packet) (72,085 bytes).
8. **Open Replay via Real Launcher (Unmocked Witness):**
   - Clicked Open Replay via direct Python handler invocation (`designer._on_open_replay()`), invoking the unmocked launcher `open_pygame_client_direct` without interception.
   - Subprocess spawned: `['.venv/Scripts/python.exe', '-m', 'battle_client.cli', '--replay', '.../replay.jsonl', '--renderer', 'pygame', '--tick-delay', '0.02', '--trace', '.../trace.jsonl']`.
   - Native Pygame window was detected by Win32 API:
     `HWND = 15860306, PID = 32608`, Title: `"Bytefray — Experimental sensing replay"`.
9. **Exercise Viewer Controls (Posted Win32 Messages vs Confirmed SDL State Changes):**
   - Posted Win32 keyboard messages (the retained workflow script supplies zero keyboard lParam) and mouse events to HWND 15860306:
     - Space: Play and pause toggling.
     - Right Arrow: Step forward across Observation -> Action -> Tick End phases.
     - Left Arrow: Reverse seeking.
     - '+': Increase playback speed (`VK_OEM_PLUS`).
     - '-': Decrease playback speed (`VK_OEM_MINUS`).
     - '1': Switch to Omniscient perspective (`Omniscient — full world state`).
     - '2': Switch to Entrant perspective (`Agent A — delivered information`).
     - Mouse click on timeline rect (x=500, y=660) for timeline scrub.
     - Home: Restart playback.
     - End: Jump to terminal outcome.
   - *Evidence Distinction & Focused Witness Resolution:* In the original 13-step workflow witness, posting Win32 messages established a dispatch attempt to the native Pygame subprocess without faulting, hanging, or crashing, and handled `WM_CLOSE` with exit code 0. To definitively confirm intra-process state mutations in an unmocked launched viewer window, a dedicated native witness ([tools/qualification/run_native_viewer_control_witness.py](../../tools/qualification/run_native_viewer_control_witness.py)) was executed. Through real Win32 screenshot comparison across discrete sub-tick phases and live playback, this confirmed authentic pixel mutations (8,398 / 10,231 / 33,431 pixels) directly caused by input processing in the live Pygame window (see Section 4.4).
10. **Close Viewer Normally:**
    - Sent `WM_CLOSE` to HWND 15860306. Window closed cleanly; child process terminated exit code 0.
11. **Edit Parameters and Rerun (Authoring Workflow Parameter Contrast):**
    - Modified in Advanced tab `Agent Params`: `search_interval = 3`, `move_step = 16`.
    - Switched to `Match Setup` and clicked Run. Second match completed: Result ID `result_3f97e20f697ac0d1e82bd346`.
    - Second result recorded new parameters `{"search_interval": 3, "move_step": 16}`.
    - First result `result_228415a9fd518026efac41c4` preserved intact in its separate directory with `{"search_interval": 2, "move_step": 32}`. Screenshot: `07_second_match_completed.png` (local-only original; hash in evidence packet) (73,088 bytes).
    - *Provenance Note:* These authoring workflow matches deliberately exercised parameter editing (`move_step = 32` and `16`). In contrast, the canonical teaching demonstration screenshots (Section 4) use the default starter parameter `move_step = 64`.
12. **Close Application:** `designer.close()` executed cleanly; Qt event loop exited 0.

---

## 4. Real SDL Playback and Interaction Evidence

The pedagogical sensing sequence was qualified and screenshotted using the authoritative Window Scout Teaching Demonstration match (`run_sensing_demo` from `battle_engine.sensing_demo`) rendered through the Pygame sensing replay viewer (`battle_client.renderers.sensing_renderer.SensingReplayRenderer`).

### 4.1 Screenshot Provenance and Workflow Relationship

- **Canonical Demonstration Provenance:** Teaching sequence screenshots `A_before_sensing.png` through `H_terminal_outcome.png` originate from the canonical teaching demonstration fixture (`run_sensing_demo`), pitting `v6_window_scout` (anchor 0) against `v6_stationary_opponent` (anchor 91) under Ruleset `bytefray-rules-6-alpha1` with canonical default starter parameters (`search_interval = 4`, `move_step = 64`) for 100 ticks (seed 0, arena 512, Q=8).
- **Contrast with Native Authoring Workflow:** These teaching screenshots do **NOT** originate from the Native Designer Authoring Workflow matches described in Section 3. The Section 3 authoring workflow deliberately edited parameters to test custom configuration (`move_step = 32` for Match 1, and `move_step = 16` for Match 2) against `v4_scout`. In contrast, the canonical teaching match demonstrates `MOVE(+64)` in Step D (`D_move_action.png`) because `move_step = 64` is the default parameter authored in `v6_window_scout/agent.yaml`.
- **Partitioned Qualification Roles:**
  - **Screenshots `01`–`07` (Group 1):** Authoring lifecycle qualification (AC9) — agent copying, capability mismatch rejection on v4, alpha1 validation, parameter configuration, supervised execution, and settings-change labeling in Qt Agent Designer.
  - **Screenshots `A`–`H` (Group 2):** Sensing exchange and perspective qualification (AC1–AC8) — dark arena initial observation, pending SENSE request, delayed anonymous receipt delivery, informed movement, reach-checked WRITE, non-tracking historical memory aging, omniscient verification badges, and terminal match resolution.

All 8 teaching frames were verified and captured to [docs/screenshots/v6_alpha1_windows/](../screenshots/v6_alpha1_windows/):

```text
A_before_sensing.png       (51,029 bytes) — Own anchor 0, own core 0..7, opponent unobserved.
B_sense_request.png        (57,397 bytes) — SENSE(91) request ring, pending status, 1 action cost.
C_delayed_receipt.png      (78,933 bytes) — Anonymous historical sample (91,), sample t1 c1, delivery t1 c2.
D_move_action.png          (78,423 bytes) — Legal MOVE(+64) arrow toward 91, anchor 0 -> 64.
E_write_action.png         (77,907 bytes) — WRITE(91, 0x42) marker applied in reach; no hit fabricated.
F_historical_knowledge.png (82,318 bytes) — Aged sample at 91 (age 1 tick / 9 callbacks); does not track opponent.
G_omniscient_view.png      (36,113 bytes) — Full world state, operator verification badges displayed.
H_terminal_outcome.png     (80,875 bytes) — Recorded end outcome: winner None; tick_limit.
```

### 4.2 Detailed Verification Findings:

1. **Step A (Before Sensing — Tick 0 / Tick 1 Callback 1 Observation):**
   - Marker: `SensingMarker(kind='own', address=0, text='Own main')`.
   - Text: `"Opponent state unknown outside delivered historical samples."`
   - Arena: Displayed as dark unknown territory. Zero opponent markers or anchor hints.
2. **Step B (SENSE Request — Tick 1 Callback 1 Action):**
   - Action: `AgentAction(kind=SENSE, operand=91)`.
   - Marker: `SensingMarker(kind='request', address=91, half_width=27)`.
   - Text: `"Callback 1: SENSE 91 APPLIED; Search requested; 1 action spent; result pending"`.
   - Leakage check: Sampled contact `(91,)` is **NOT** displayed on screen during this action phase.
3. **Step C (Delayed Receipt — Tick 1 Callback 2 Observation):**
   - Marker: `SensingMarker(kind='receipt')` and `SensingMarker(kind='historical', address=91)`.
   - Text: `"Anonymous sample at 91; sampled t1 callback 1, received t1 callback 2; age 0 ticks / 1 own callbacks"`.
   - Scan history: `"Scan positive: center 91 +/- 27; anonymous addresses (91,); process main; sampled t1 callback 1; received t1 callback 2"`.
4. **Step D (Informed MOVE — Tick 1 Callback 2 Action):**
   - Action: `AgentAction(kind=MOVE, operand=64)`.
   - Marker: `SensingMarker(kind='move', origin=0, address=64)`.
   - Anchor updated: 0 -> 64. Contact 91 retained as historical reference point.
   - Parameter relationship: Reflects default `move_step = 64`.
5. **Step E (Optional WRITE — Tick 1 Callback 3 Action):**
   - Action: `AgentAction(kind=WRITE, operand=91, value=66)`.
   - Marker: `SensingMarker(kind='write', address=91, text='WRITE APPLIED')`.
   - Text: `"Callback 3: WRITE 91 APPLIED value=66; Recorded own action"`.
   - Truthfulness check: No claims of core discovery, player identity, or disruption hit.
6. **Step F (Historical Knowledge Retention — Tick 2 Callback 9 Observation):**
   - Marker: `SensingMarker(kind='historical', address=91)`.
   - Age text: `"age 1 ticks / 9 own callbacks"`.
   - Non-tracking check: Opponent's live movements do not update this historical diamond.
7. **Omniscient Mode Labeling:**
   - Permanent top banner explicitly labels: `"1: Omniscient — full world state"`.
   - Shows operator verification report:
     `artifact consistency=True; independent reconstruction=True; teaching complete=True; filtered perspective available=True; demo sidecar verified=True`.
8. **Isolation & View Switching:**
   - Switching between Omniscient (key '1') and Entrant (key '2') resets scroll offsets and strips all omniscient information from the entrant viewport. No camera, tooltip, or row count leakage.

### 4.3 Confirmed SDL and Controller State Changes Evidence

Unlike external Win32 message posting, functional SDL state mutations were verified via direct in-process assertions in `client/tests/test_v6_alpha_m1_5.py`:

- **Pause Toggle:** Verified in `test_pygame_surface_events_navigation_switching_and_rewind`. Pressing Space pauses playback; invoking `presentation.controller.update(100)` confirms `presentation.index == 2` remains unchanged, proving the playhead is frozen.
- **Phase Stepping:** Verified discrete cursor progression through sub-tick phases. Successive `pg.K_RIGHT` events advance `presentation.position` and `renderer.last_markers` sequentially from empty -> `request` -> `receipt`/`historical` -> `move` -> `write`.
- **Reverse Seeking & Rewind:** `pg.K_HOME` confirms complete reset of historical markers (`not any(m.kind == "historical"...)`) and resets `presentation.terminal_text is None`.
- **Timeline Scrubbing:** Mouse button event at `(1080, 660)` on timeline rect triggers `seek_from_mouse` and confirms `presentation.at_end == True`.
- **Speed Adjustment:** `pg.K_PLUS` updates `presentation.speed == 2`.
- **Perspective Switching:** Key `1` switches to Omniscient view, clearing entrant scene lines (`renderer.last_lines == ()`); key `2` restores Entrant view with exact byte-for-byte pixel match (`pg.image.tobytes(renderer.screen, "RGB") == receipt_pixels`).
- **Real SDL Render Loop:** `test_real_sdl_sensing_loop_with_queued_interaction` executes `cli.main(["--renderer", "pygame", "--replay", ..., "--paused"])` through the real Pygame event loop, confirming 13+ rendered frames and authentic on-disk frame captures (`receipt.png`, `request.png`, `write.png`).

### 4.4 Confirmed Native Subprocess Viewer Control Processing Evidence (Real Screenshot Comparison)

Pursuant to the final qualification gate requirement to determine whether the actual launched viewer processed Win32 messages and show confirmed intra-process state mutations, a dedicated unmocked witness tool was authored and executed: [tools/qualification/run_native_viewer_control_witness.py](../../tools/qualification/run_native_viewer_control_witness.py).

#### Execution Conditions:
- **Subprocess Command:** `.venv/Scripts/python.exe -m battle_client.cli --replay .../replay.jsonl --renderer pygame --paused`
- **Native Window Target:** `HWND = 31260776, PID = 32352`, Title: `"Bytefray — Experimental sensing replay"`
- **Display Driver:** Native Windows video driver (`pygame-ce 2.5.8 / SDL 2.32.10`), desktop resolution 2048 x 1152.
- **Capture Mechanism:** Unmocked Win32 window grab (`screen.grabWindow(hwnd)` via PySide6/QGuiApplication) capturing authentic on-screen client pixels before and after discrete Win32 input message dispatch.
- **Clean Termination:** Sent `WM_CLOSE` to HWND; child process terminated with exit code 0.

#### Confirmed State Mutations and Pixel Comparison Results:
1. **Frame 1 — Initial Paused Boundary (`witness_control_01_initial_observation.png`, 69,512 bytes):**
   - Paused initial view in Entrant perspective at Tick 0, TICK_END.
   - Canvas displays dark unknown territory with own core at 0..7 and anchor at 0; status bar reads `Paused / 1x`.
2. **Frame 2 — Stepped Forward to Callback 1 Observation Phase (`witness_control_02_stepped_action_phase.png`, 74,167 bytes):**
   - Dispatched Win32 `WM_KEYDOWN` + `WM_KEYUP` with `VK_RIGHT` (Right Arrow key, scancode 0x4D with extended flag).
   - **Confirmed Intra-Process Mutation:** The launched Pygame subprocess processed the event through SDL, advanced `SensingPresentation.controller` from Tick 0 TICK_END to Tick 1 Callback 1 OBSERVATION phase, updating the HUD to `"Callback 1: OBSERVATION ; Delivered observation"`.
   - **Pixel Difference (Frame 1 -> Frame 2):** **8,398 differing pixels**.
3. **Frame 3 — Stepped Forward to SENSE Request Action Phase (`witness_control_03_stepped_delayed_receipt.png`, 80,824 bytes):**
   - Dispatched Win32 `WM_KEYDOWN` + `WM_KEYUP` with `VK_RIGHT` again.
   - **Confirmed Intra-Process Mutation:** The launched Pygame subprocess advanced cursor position to Tick 1 Callback 1 ACTION phase, drawing the yellow SENSE request ring at anchor 91 (`SENSE / pending`), rendering reach boundary indicators, and updating the action banner (`"Callback 1: SENSE 91 APPLIED; Search requested; 1 action spent; result pending"`).
   - **Pixel Difference (Frame 2 -> Frame 3):** **10,231 differing pixels**.
4. **Frame 4 — Active Playback Clock Advancement (`witness_control_04_playback_active.png`, 104,521 bytes):**
   - Dispatched Win32 `WM_KEYDOWN` + `WM_KEYUP` with `VK_SPACE` (Space key, scancode 0x39).
   - **Confirmed Intra-Process Mutation:** The launched Pygame subprocess toggled `PhasePlaybackController` from `Paused / 1x` to `Playing / 1x`; the clock progressed continuously across callbacks 2..6, moving the anchor to 64, rendering the delivered historical diamond at anchor 91 (`sample 91`), and populating the scan history panel at Tick 1 Callback 7 OBSERVATION phase.
   - **Pixel Difference (Frame 3 -> Frame 4):** **33,431 differing pixels**.

#### Summary of Retained Screenshots:
All 4 witness screenshots were saved to [docs/screenshots/v6_alpha1_windows/](../screenshots/v6_alpha1_windows/), alongside the 15 previously qualified screenshots (`01`–`07` and `A`–`H`), which remain preserved byte-for-byte untouched:
```text
witness_control_01_initial_observation.png (69,512 bytes) — Paused Tick 0 TICK_END initial state
witness_control_02_stepped_action_phase.png    (74,167 bytes) — Stepped to Tick 1 Callback 1 Observation (diff: 8,398 px)
witness_control_03_stepped_delayed_receipt.png (80,824 bytes) — Stepped to Tick 1 Callback 1 SENSE action (diff: 10,231 px)
witness_control_04_playback_active.png         (104,521 bytes) — Unpaused live playback to Tick 1 Callback 7 (diff: 33,431 px)
```

---

## 5. Replay Fallback and Negative Failure Behavior

The following six failure/fallback categories were covered across the standalone witness and focused tests; they are not six cases in one standalone run. The script supplies four negative checks, one positive capability check and repeated-run determinism. Evidence: [run_determinism_and_neg_cases.py](../../tools/qualification/run_determinism_and_neg_cases.py) and [client/tests/test_v6_alpha_m1_5.py](../../client/tests/test_v6_alpha_m1_5.py):

1. **Missing Trace:**
   - `load_sensing_presentation(session, replay, None)` returned `presentation is None`.
   - Safe fallback reason: `"Omniscient — replay only. Trace unavailable; delivered perspective disabled."`
   - ReplaySession remains loaded; raw path/directory strings are not leaked in the reason string.
2. **Corrupted Trace (Digest Mismatch or Truncated JSON):**
   - Returned `presentation is None`.
   - Reason: `"Omniscient — replay only. Exchange evidence invalid; delivered perspective disabled."`
   - Unverified exchange playback is completely disabled.
3. **Invalid Demonstration Sidecar:**
   - Created `demo.json` with invalid schema payload.
   - Result: Replay and trace load successfully; `presentation.sidecar_verified == False`.
   - Notice displayed: `"Optional demonstration invalid; factual replay remains available."`
   - No crash or silent validation claim.
4. **Internally Consistent but Incomplete Teaching Exchange:**
   - Evaluated agent executing READs without SENSE:
     `artifact_pair_consistent == True`, `exchange_reconstructed == True`, `knowledge_projected == True`.
     `teaching_complete == False`, `sidecar_verified == False`.
   - **No false success claim is awarded to an incomplete teaching sequence.**
5. **Incompatible Ruleset / Capability Selection:**
   - Loaded stable v4 replay: rejected by `load_sensing_presentation` with safe fallback reason.
   - Validated agent declaring `sense` under v4 in Designer: rejected at load stage before execution.
6. **Changed Source Revision / Parameter Modification:**
   - Tested in `test_v6_alpha_m1_5_adversarial_designer.py`: modifying source after validation clears the cached verdict; modifying parameters in Advanced labels earlier results as "earlier settings" while keeping original artifacts fully accessible.

---

## 6. Windows Native Qt Diagnostic Disposition (0x8001010d)

The retained M1-5 Windows Qt diagnostic was investigated in depth:

```text
Diagnostic Code: 0x8001010d (RPC_E_CANTCALLOUT_ININPUTSYNCCALL)
Win32 COM Meaning: "An outgoing call cannot be made since the application is dispatching an input-synchronous call."
```

### 6.1 Established Evidence and Facts:

1. **Observed Nonblocking Result:**
   - In all testing contexts—including the full 13-step native authoring workflow ([tools/qualification/run_native_designer_workflow.py](../../tools/qualification/run_native_designer_workflow.py)), pytest GUI test runs (`test_linux_designer_smoke.py`, `test_agent_development_validate.py`), and standalone Qt scripts—the application never crashes, aborts, or hangs.
   - The accepted workflow displayed windows and completed its child processes. These observations do not measure event latency or prove that every posted control changed state.
2. **External Bare-QWidget Reproduction:**
   - A standalone, minimal script displaying a bare `QWidget` with zero Bytefray imports or application code reproduces the exact same diagnostic output under Windows.
   - This supports a Windows / PySide6 / Qt integration origin independent of Bytefray. It does not identify the initiating component or prove a complete COM call chain.
3. **Vectored Exception Handling Interception:**
   - When Python's `faulthandler` module is active (enabled by default in `pytest`), it registers a Windows Vectored Exception Handler (`AddVectoredExceptionHandler`).
   - During native Qt window display and focus changes (`WM_CREATE`, `WM_SHOWWINDOW`, `WM_ACTIVATEAPP`), first-chance Structured Exception Handling (SEH) exceptions carrying HRESULT `0x8001010d` are intercepted by `faulthandler` and reported to `stderr` as `Windows fatal exception: code 0x8001010d`.
   - The qualified processes continued and exited successfully. Internal exception handling and the precise initiating caller remain unproven without a native callstack.

### 6.2 Residual Root-Cause Uncertainty:

- While `0x8001010d` formally indicates an outgoing COM call attempted during an input-synchronous message call, the exact Windows OS subsystem or third-party hook initiating the call (e.g. Windows UI Automation provider, Windows Accessibility subsystem, Input Method Editor / IME hook, or DWM focus transition) has not been isolated down to a specific DLL callstack.
- The observed diagnostic is nonblocking in these runs; the bare-QWidget reproduction supports an integration origin. The exact COM caller, initiating subsystem and full root cause remain uncertain.

### 6.3 Disposition:

- **Classified as an EXTERNAL, NONBLOCKING Windows COM platform diagnostic with residual root-cause uncertainty.**
- It does not block any application functionality, authoring workflow, or qualification test.
- Retained as an observed Windows integration diagnostic; no specific DLL, hook or upstream defect is asserted.

---

## 7. Deterministic Teaching Reproduction Evidence

Two independent runs of `run_sensing_demo` were executed with identical teaching inputs (seed 0, arena 512, Q=8, limit 100 ticks, Window Scout at 0, Stationary Opponent at 91) into directories `.pytest-tmp/det_and_neg_cases/run1` and `.pytest-tmp/det_and_neg_cases/run2`:

```text
Run 1 Result: is_verified=True, steps=4, winner=None, ticks=100
Run 2 Result: is_verified=True, steps=4, winner=None, ticks=100

Replay Lines Count: 103 vs 103
Replay Line Diff Count: 0 (Exact byte-for-byte equality across all 103 lines)

Trace Records Count: 1,600 vs 1,600
Trace Logical Mismatches (excluding wall_time_ms): 0
Total Logical Differences: 0

Demo Sidecar Comparison:
  schema: equal (bytefray.sensing_demo)
  schema_version: equal (1)
  provenance: equal (product_teaching_demo)
  ruleset_id: equal (bytefray-rules-6-alpha1)
  match_config: equal
  teaching_steps: equal (all 4 steps identical)
  scout_capture_complete: True
  opponent_capture_complete: True
  initial_fingerprint == python_subset_fingerprint: True
```

The two completed runs of the captured canonical teaching inputs matched in logical world states, ordered decisions, observations and terminal outcome. This evidence does not certify arbitrary editable Python agents as deterministic.

---

## 8. Windows Regression Campaign Results

### 8.1 Static Quality Checks

- **Ruff Lint:** `python -m ruff check .` -> **PASSED** (`All checks passed!`), including the four finalized qualification scripts. An initial closure lint invocation traversed the newly generated test snippets (32 deliberate undefined-name negatives and 8 unsorted scripted-agent imports). Those temporary workspaces were preserved under ignored `work/m1_6a_closure_20261011/generated_test_workspaces/`; unchanged repository files then passed ordinary `ruff check .`. No rule or assertion was disabled.
- **Engine Type Check:** `python -m mypy engine/src/battle_engine` -> **PASSED** (`Success: no issues found in 102 source files`).
- **Client Type Check:** `python -m mypy client/src/battle_client` -> **PASSED** (`Success: no issues found in 19 source files`).
- **Git Formatting:** starting checks passed; the final staged allowlist is checked with `git diff --cached --check` before the staging report.

### 8.2 Test Suite Execution and Evidence Reconciliation

#### Evidence Reconciliation on Test Totals:
The earlier report draft claimed a summary figure of "934+ tests executed," calculated by combining an unverified "Broad Product Regression Selection" entry of 821 with 106 Designer GUI tests and 7 Client GUI tests (821 + 106 + 7 = 934). That "821" entry was an unverified count that conflated historical repository file counts (821 files at Phase 0) with test executions; that specific command was not executed as a distinct verified run in that form.

Each run is reported below in its own scope. Focused selections overlap the broad selection and each other. Witness steps and screenshot frames are not pytest cases. No aggregate execution count is used as a coverage claim.

| Test Suite / Scope | Invocations & Commands | Tests Executed | Passed | Failed | Errors | Skipped / Deselected |
|---|---|---|---|---|---|---|
| **Broader Windows Product Regression Complement** | Exact 114 engine modules plus `_legacy/tests` and `client/tests`; retained [node inventory](evidence/m1_6a_windows/regression_nodes.txt) | 3,218 | **3,199** | 0 | 0 | 19 skipped, 7 deselected (`gui`) |
| **Client Headless Suite** | `pytest client/tests -q` | 550 | **550** | 0 | 0 | 7 deselected (`gui`) |
| **Earlier Client GUI-marked Selection (reported)** | `pytest client/tests -m gui -v` | 7 | **7** | 0 | 0 | 550 deselected (`not gui`) |
| **Earlier Designer GUI Selection (reported)** | `pytest tests/ -m gui (6 focused modules) -q` | 106 | **106** | 0 | 0 | 0 |
| **Focused M1-5 Client Tests** | `pytest client/tests/test_v6_alpha_m1_5*.py tests/test_v6_alpha_m1_5_adversarial_designer.py -m ""` | 21 | **21** | 0 | 0 | 0 |
| **Independent Adversarial Selection** | `pytest tests/test_v6_alpha_m1_5_adversarial_designer.py client/tests/test_v6_alpha_sensing_adversarial.py -m ""` | 12 | **12** | 0 | 0 | 0 |
| **M1-1 Policy & Capabilities** | `pytest engine/tests/test_v6_alpha_m1_policy_capabilities.py` | 42 | **42** | 0 | 0 | 0 |
| **M1-2 Window Scout Teaching Demo** | `pytest engine/tests/test_v6_alpha_m1_2_window_scout.py` | 19 | **19** | 0 | 0 | 0 |
| **M1-3 Sensing Playback Verification** | `pytest engine/tests/test_v6_alpha_m1_3_sensing_playback.py` | 30 | **30** | 0 | 0 | 0 |
| **M1-4 Knowledge Projection & Adversarial** | `pytest client/tests/test_v6_alpha_sensing*.py` | 29 | **29** | 0 | 0 | 0 |
| **Stable v4 Immutability & Equivalence** | `pytest engine/tests/test_v4_historical_immutability.py engine/tests/test_v4_stable_ruleset_equivalence.py` | 32 | **32** | 0 | 0 | 0 |
| **Native Windows Authoring Workflow Witness** | `python tools/qualification/run_native_designer_workflow.py` | 13 contract actions (grouped) | **13** | 0 | 0 | 0 |
| **Native Viewer Control Processing Witness** | `python tools/qualification/run_native_viewer_control_witness.py` | 4 frames | **4** | 0 | 0 | 0 |
| **Deterministic & Negative Cases Qualification Witness** | `python tools/qualification/run_determinism_and_neg_cases.py` | 6 check groups (determinism + four negatives + one positive) | **6** | 0 | 0 | 0 |

*Note on test counts and overlap:* The broader product regression complement (3,218 collected, 3,199 passed) encompasses the engine and client headless suites; focused M1-5 tests (21), independent adversarial tests (12), and M1-4 tests (29) are targeted subsets drawn from `client/tests` and `tests/`. No failures/errors were reported in the accepted runs. Closure JUnit results and the 19 broad skips are independently reconciled below.

#### Broader Headless Regression Status — Obligation Resolved and Verified:
- **Confirmation & Selection Count:** The outstanding broader Windows headless product regression complement was fully executed across the verified product selection: `_legacy/tests` (2 tests), `client/tests` (550 tests), and 114 non-research `engine/tests` suites (2,666 tests), collecting exactly **3,218 tests** (with 7 GUI tests deselected under `-m "not gui"`).
- **Execution Environment:** Executed under native Windows AMD64 Python 3.13.14 via `pytest` with repo-local `--basetemp=.pytest-tmp/m1_6a_regression`.
- **Results Summary:**
  - **3,199 passed**
  - **19 skipped** (all accounted for below)
  - **7 deselected** (`gui` display-backed tests)
  - **0 failures, 0 errors**
  - **Duration:** 380.62s (6.34m)
  - **Exit Code:** 0
  - **Retained JUnit XML:** `work/m1_6a_windows_regression_final.xml` (467,637 bytes)
  - **Retained Log:** `work/m1_6a_windows_regression_final.log` (3,705 bytes)
- **Skip Reconciliation (All 19 Accounted For):**
  1. *Windows symlink privilege unavailable (11 skips) plus POSIX-only symlink semantics (1 skip):*
     - `engine/tests/test_agent_evaluation_revision_capture.py::test_evaluation_captures_symlink_cycle_as_revision_omissions`
     - `engine/tests/test_agent_package.py::test_export_preflights_large_internal_file_symlink_before_reading_target`
     - `engine/tests/test_agent_revisions.py::test_symlink_cycle_is_reported_as_deterministic_omissions`
     - `engine/tests/test_agent_revisions.py::test_external_file_symlink_is_reported_not_silently_dropped`
     - `engine/tests/test_agent_revisions.py::test_internal_file_symlink_is_dereferenced_and_included`
     - `engine/tests/test_agent_revisions.py::test_broken_symlink_is_reported_not_a_file`
     - `engine/tests/test_agent_revisions.py::test_completeness_and_fingerprint_reflect_omissions`
     - `engine/tests/test_agent_revisions.py::test_verify_revision_accounts_for_recorded_omissions`
     - `engine/tests/test_evaluation_history_verification.py::test_resolve_contained_path_rejects_symlink_escape`
     - `engine/tests/test_evaluation_history_verification.py::test_verify_cell_rejects_symlink_escape_replay_filename`
     - `engine/tests/test_launchers.py::test_source_commands_do_not_resolve_a_symlinked_interpreter` (POSIX symlink semantics only)
     - `engine/tests/test_replay_integrity.py::test_replay_symlink_escape_is_rejected_where_supported`
  2. *Windows NTFS colon alternate data streams (1 skip):*
     - `engine/tests/test_agent_package.py::test_export_rejects_nonportable_live_payload_name_before_read`
  3. *Unbuilt frozen executable smoke tests / `BYTEFRAY_FROZEN_EXE` unset (6 skips):*
     - `engine/tests/test_frozen_bytecode_exclusion.py::test_frozen_payload_contains_no_python_bytecode`
     - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_executable_creates_every_supported_variant[api2-annotated]`
     - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_executable_creates_every_supported_variant[api2-blank]`
     - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_executable_creates_every_supported_variant[api2-window_scout]`
     - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_executable_bundles_every_supported_template_directory`
     - `engine/tests/test_frozen_scaffold_resources.py::test_frozen_smoke_is_not_silently_satisfied_by_the_source_tree`
- **Historical Partition Reconciliation:** Pursuant to M1-1 Disposition 03, the 72 frozen historical nodes remain authorized in their separately preserved baseline environment (`work/m1_1_archive_20261010/baseline_frozen_71.xml`, 71 passed, + 1 in isolated guard process = 72 passed). All 329 raw pins match the preserved baseline checkout at `b948540`; 11 pinned product files in the current checkout differ through the unchanged M1-1/M1-2 commits, as expected. Zero research files were modified since M1-1; zero locked E9 scientific operations were executed.
- **Obligation Closure:** The outstanding broader Windows regression obligation is formally **RESOLVED AND CLOSED**.


### 8.3 Final inventory reconciliation: exact 906-case difference

The retained M1-1 current JUnit inventory and final M1-6A JUnit identify the
following exact set difference. These 21 modules have no source changes since
the M1-1 commit. Their saved per-module counts sum to **906**: E2–E6
semantic/context modules **328**, V6 research Ruleset modules **519**, and V5
research modules **59**. Thus **3,218 + 906 = 4,124**. The earlier figure
included research/experiment modules that the final campaign excluded; calling
all 4,124 cases product tests was incorrect. No original 4,124 collection
command survives in the retained packet, so its historical command/filter is
not claimed. The exact count difference is reproducible from saved inventories.

| Module under `engine/tests/` | Cases in the 906 difference |
| --- | ---: |
| `test_e2_capture_hold_semantics.py` | 26 |
| `test_e3_slot_limited_disruption_semantics.py` | 73 |
| `test_e4_mirrored_pass_order_semantics.py` | 94 |
| `test_e5_anchor_placement_semantics.py` | 44 |
| `test_e6_context_detection_radius.py` | 45 |
| `test_e6_priced_sensing_semantics.py` | 46 |
| `test_ruleset_v6_research_anchor_before_core.py` | 84 |
| `test_ruleset_v6_research_capture_hold.py` | 37 |
| `test_ruleset_v6_research_disruption_slot.py` | 57 |
| `test_ruleset_v6_research_mirrored_passes.py` | 80 |
| `test_ruleset_v6_research_scale.py` | 47 |
| `test_ruleset_v6_research_scale_move.py` | 35 |
| `test_ruleset_v6_research_scale_move_proportional.py` | 28 |
| `test_ruleset_v6_research_sensing.py` | 82 |
| `test_ruleset_v6_research_sensing_active.py` | 69 |
| `test_v5_research_analyzer.py` | 7 |
| `test_v5_research_r1_metrics.py` | 2 |
| `test_v5_research_r3_agents.py` | 9 |
| `test_v5_research_r3_metrics.py` | 6 |
| `test_v5_research_r4_agents.py` | 26 |
| `test_v5_research_r4_population.py` | 9 |

The broad selection comprises **114 engine modules / 2,666 cases**, **20
client modules collected / 550 headless cases** (19 contribute headless cases;
one module contains only GUI cases), and **one legacy module / 2 cases**.
The default `not gui` marker deselected seven cases, so pre-marker collection
was 3,225 and executed/skip-accounted JUnit cases were 3,218. The original log's
"115 test suites" launcher message is not an authoritative module count.
[Exact module selection](evidence/m1_6a_windows/regression_modules.txt) and
[all 3,218 case identities](evidence/m1_6a_windows/regression_nodes.txt) are retained.

All **123 excluded engine modules** are listed and classified in
[inventory.json](evidence/m1_6a_windows/inventory.json). Outside the required
compatibility subset, exclusions cover research Ruleset treatments, E2–E9
study analyzers/pipelines/authority/instruments, experiment harnesses and V5
research metrics/agents. Those study operations are outside M1 Windows product
qualification. The exclusions are run selections, not new skip/xfail or
collection configuration, and do not imply a current unpartitioned full-suite
PASS. Disposition 03's 72 historical nodes remain separately qualified.

### 8.4 Required omitted coverage: resolved in a separate run

Filename-based research exclusion did conceal required current inventory and
Alpha 1 compatibility coverage. The audit selected every registry-wide/lifecycle
check in the affected Ruleset modules, the direct/worker radius and window
matrices, E8 compatibility-gate inventory/rejection checks, and the complete
unchanged E8 parent-byte, sensing/context and trace characterizations required
by AC10. This includes the 12 authorized M1-1 inventory/context functions
outside the broad selection; the thirteenth, in `test_ruleset_policy.py`, was
already in the broad run. No historical partition node is in the supplement.
These compatibility tests import existing E8 characterization helpers and use
fixed synthetic/infrastructure inputs in the isolated test workspace. That is
distinct from product/demo isolation: no E8/E9 study execution, seed reveal,
payoff campaign or authority event was performed.

| Supplemental module | Exact selected cases |
| --- | ---: |
| `test_e6_context_detection_radius.py` | 32 |
| `test_ruleset_v6_research_anchor_before_core.py` | 5 |
| `test_ruleset_v6_research_capture_hold.py` | 4 |
| `test_ruleset_v6_research_disruption_slot.py` | 5 |
| `test_ruleset_v6_research_mirrored_passes.py` | 6 |
| `test_ruleset_v6_research_scale.py` | 1 |
| `test_ruleset_v6_research_scale_move.py` | 1 |
| `test_ruleset_v6_research_scale_move_proportional.py` | 1 |
| `test_ruleset_v6_research_sensing.py` | 5 |
| `test_ruleset_v6_research_sensing_active.py` | 23 |
| `test_v6_e8_family.py` | 20 |
| `test_v6_e8_parent_byte_identity.py` | 99 |
| `test_v6_e8_sensing_context.py` | 44 |
| `test_v6_e8_sensing_semantics.py` | 58 |
| `test_v6_e8_traces.py` | 24 |

**Separate supplemental result:** **328 passed**, zero skips/deselections,
failures/errors/xfails; JUnit time **89.322s**. Selection is
[supplemental_nodes.txt](evidence/m1_6a_windows/supplemental_nodes.txt), result is
[supplemental_compatibility.xml](evidence/m1_6a_windows/supplemental_compatibility.xml).
Execution used `pytest.main` with those exact nodes, ordinary headless marker,
`-p no:cacheprovider`, a fresh repo-local `--basetemp`, and a separate JUnit
path. An initial subprocess launch exceeded Windows command length before any
test ran; its failed launch remains in the audit trail. No test failure was
bypassed. The original 3,218-case campaign was not rerun.

**GUI deselections:** The seven exact nodes are retained in
[gui_nodes.txt](evidence/m1_6a_windows/gui_nodes.txt). The earlier report states
seven passed separately; its original run-specific XML/log was not retained in
the accessible packet. Closure therefore executed those same seven cases as a
new, explicitly separate evidence run: `client/tests -m gui` under native
Windows SDL, **7 passed, 550 deselected**, zero skips/failures/errors/xfails in
**2.76s** (JUnit **2.718s**). Result:
[client_gui.xml](evidence/m1_6a_windows/client_gui.xml). This does not replace or
relabel the earlier run. Four cases exercise native windows with injected test
events, two exercise surfaces, and one mocks window/loop fallback boundaries;
seven GUI markers do not establish seven independent manual interactions.

**Skip classification correction:** The broad JUnit proves **11 Windows
symlink privilege skips**, **1 POSIX-only symlink semantics skip**, **1 NTFS
colon/ADS skip**, and **6 unset frozen-executable skips**. The earlier "12
unprivileged symlink" category conflated the POSIX-only case. Every node and
reason category is retained in `inventory.json`. Frozen executable lifecycle
qualification is later alpha-wide scope under the contract, not M1 closure.
Both new closure runs retained the nonblocking cacheprovider/config warning;
this is not a skipped test or suppressed failure.

No required current Windows product module or required Alpha 1 compatibility
case remains omitted. The 72 frozen-baseline cases retain the adopted M1-1
Disposition 03 result: 71 in preserved baseline JUnit plus the separately
passed existing-plugin guard case. No E9 operation or new authority is inferred.

---

## 9. Player Experience Review

1. **Selecting Experimental Sensing:** Clear and discoverable. The ruleset dropdown explicitly states `V6 alpha1 — Experimental sensing (bytefray-rules-6-alpha1)`. Capability mismatches under stable v4 are explained clearly with guidance to choose alpha1.
2. **Window Scout Parameters:** Controlled via bounded integer spinners with explicit ranges (`search_interval`: 1..16, `move_step`: 1..64). Default values (4 and 64) provide immediate working examples.
3. **Action Cost:** Clearly indicated in the action log (`"Search requested; 1 action spent; result pending"`) and action counters.
4. **Delayed Delivery:** Pedagogically intuitive. The observation following a SENSE displays `"Receipt now: positive"`, `"Anonymous sample at 91; sampled t1 callback 1, received t1 callback 2"`.
5. **Anonymous Contact Meaning:** Displayed as an anonymous diamond without revealing player name, core location, or ownership.
6. **Historical Sample Staleness:** The sample diamond does not follow the opponent when they move; it displays age (`age 1 ticks / 9 own callbacks`), teaching that sensing yields historical snapshots rather than active tracking.
7. **Omniscient vs. Entrant View:** The two perspectives are unmistakably distinct: Entrant view features an unknown dark arena with delivered facts only; Omniscient view exposes all cores, anchors, and operator verification badges.
8. **Controls & Pacing:** Familiar and responsive (Space for play/pause, arrows for discrete phase stepping, timeline dragging for scrub, Home/End for restart/terminal outcome).

### Usability Observations (Nonblocking):
- **Development vs. Advanced Tabs:** A newcomer attempting to modify agent parameters directly in the "Development" tab must navigate to "Advanced" to access parameter controls. The Development tab status text now guides them there, but unified parameter editing on the development panel could be considered in later milestones.
- **Scrollbar Indicator in Pygame History:** The delivered scan/read history panel supports mouse wheel scrolling, but does not render a vertical scrollbar thumb. Players must discover that the text region responds to the scroll wheel.

---

## 10. Independent Adversarial Review Findings

All 10 adversarial review axes were investigated:

1. **End-to-End Consistency:** Ruleset ID `bytefray-rules-6-alpha1`, resolved parameters, and source revisions were verified identical across native match results, replays, traces, and demo sidecars.
2. **GUI Validity & Interaction Distinction:** The unmocked workflow witness ran in real native Windows windows, spawning a live Pygame subprocess with HWND 15860306, PID 32608 (detected via FindWindowW). Direct Python handler invocation on the widget was used for replay launch; posted Win32 messages recorded input dispatch attempts and window stability; the dedicated subprocess witness separately confirms state changes and exit code 0; while confirmed SDL state mutations (pause, stepping, seeking, perspective switching) were established in-process via `test_v6_alpha_m1_5.py`.
3. **Information Leakage:** In entrant mode, `draw_entrant` receives only `SensingView`. Zero raw world state, hidden opponent actions, or unobserved counters leak into the presentation.
4. **Perspective Switching:** Switching from Omniscient to Entrant wipes the canvas and reconstructs only permitted historical facts through the active phase. Reverse seeking rebuilds only past facts.
5. **Teaching Labels:** Replays without SENSE actions are rejected for teaching completeness. Operator badges are withheld in entrant mode.
6. **Native Qt Diagnostic:** Investigated `0x8001010d`. Verified as an external, nonblocking platform diagnostic reproducing on a bare native `QWidget` without Bytefray imports. Residual uncertainty regarding the specific Windows COM caller is explicitly retained.
7. **Determinism:** Repeated completed runs produced 0 replay diffs and 0 trace logical diffs.
8. **Filesystem Isolation:** All qualification files were confined to isolated temporary paths and permanent documentation directories. No user files or settings outside the test directory were touched.
9. **Historical Integrity:** Pinned hashes and study files remain byte-for-byte identical.
10. **AC1–AC11 Completeness:** The earlier conditional AC10 finding is superseded by the retained broad result and the separate 328-case compatibility supplement. All eleven criteria are PASS for authorized Windows scope.

---

## 11. Historical and Research Preservation Confirmation

All preservation boundaries required by Section 11 remain intact:

- **E9 Scientific Execution:** **LOCKED**.
- **Requirement C:** **NOT ESTABLISHED**.
- **Research Seed Generation & Payoffs:** **ZERO** (0).
- **New G Consumption & Authority Events During Windows Qualification/Closure:** **ZERO** (0). Original G remains consumed exactly once; its history is unchanged.
- **Historical Seal-08 Pins:** **329 / 329 raw pins verified in the preserved frozen-baseline checkout**, bound to commit `b948540aa9ef34134ff7e3c633c3acfc9f97da96` with **0 mismatches**.
- **Original Study Namespace:** **1,384 files**, **967,603,996 bytes** at `runs/research_v6_e9_eb480ff7935ed2a3` (exact match).
- **External Local NTFS Backup:** **1,447 files**, **968,508,794 bytes** in the preserved local backup (exact match; private path omitted).
- **Backup Manifest Hashes:**
  - `source_manifest.json`: `b14afef092cb621494fa7a1ad38c9c0d38aafca0e58205f7c75a91048ec481f7` (verified match).
  - `ignored_cache_source_manifest.json`: `f599c0c5dc7b3c4cccbc6870e32bc6341bb1f38e1ee6c85a6d55c16914fd56df` (verified match).
- **Local Settings:** `.claude/settings.local.json` intact.

---

## 12. Defects, Severity, and Recommended Corrections

- **Defects Identified:** Zero blocking or functional defects in implemented sensing, authoring, or playback behavior.
- **Completed Regression Complement:** The broader headless regression complement across all product suites was executed pursuant to M1-1 Disposition 03 validation rules. Out of 3,218 collected tests, 3,199 passed, 19 skipped, 7 deselected, 0 failures, 0 errors in 380.62s. Zero regressions were identified. The complete JUnit report is retained at `work/m1_6a_windows_regression_final.xml` and execution log at `work/m1_6a_windows_regression_final.log`. All 19 skips were formally reconciled (11 Windows symlink privilege skips, 1 POSIX-only symlink skip, 1 NTFS colon stream skip, 6 unset frozen binary skips).
- **Completed Control Processing Obligation:** Native Pygame viewer control processing was confirmed via unmocked live subprocess execution and verified pixel divergence across tick-zero boundary, callback 1 observation, pending SENSE action, and live playback states (`witness_control_01` through `04`).
- **Diagnostic Limitation:** `0x8001010d` occurs under `pytest` with `faulthandler` during native Qt window display. Characterized as an external, nonblocking platform diagnostic reproducing on bare `QWidget` with residual uncertainty regarding the specific OS COM caller. It does not crash, hang, or impede execution.
- **Closure Corrections:** Reconciled the 906-case scope mismatch, filled the 328-case compatibility gap, retained a fresh separate seven-case GUI result, corrected skip categories, clarified control phases and COM uncertainty, and excluded private-path screenshots from staging. No product-source correction was required.

---

## 13. Authorized staged manifest and preservation boundary

The exact qualification-only staging allowlist is
[staged_manifest.txt](evidence/m1_6a_windows/staged_manifest.txt). It includes
this report, four qualification scripts, privacy-filtered evidence records and
17 authentic unchanged screenshots. Completed-match screenshots 06/07 remain
local-only because their pixels expose a private temporary path; their hashes
and accepted workflow findings are retained. No image was altered or generated.

Original `work/m1_6a_windows_regression_final.xml` and `.log`, closure logs/XML,
the pre-closure report at `work/m1_6a_closure_20261011/qualification_before_closure.md`,
and previous unsuccessful viewer captures remain local and unchanged. Exported
JUnit records explicitly document privacy filtering and bind back to original
hashes. No private E9 evidence, backup payload, generated match artifact,
local settings or unrelated file belongs to the staged allowlist.

The pre-existing empty Git index lock blocked the first staging attempt. Its
old timestamp, absence of Git processes and successful exclusive open established
a stale lock. It was preserved under the ignored local closure audit directory;
the index was unchanged before staging. No lock bytes were deleted.

Product source and all M1-1 through M1-5 commits remain unchanged. Closure
changes only qualification documentation, scripts and evidence. The viewer
witness script's comments/print labels now match the observed phases; its
original screenshot names/bytes and the qualified behavior are preserved.

## 14. Formal disposition and Linux boundary

**M1-6A WINDOWS — FORMALLY CLOSED**\
**Qualification disposition: PASS**\
**Linux M1-6B: NOT STARTED**\
**Overall M1 Alpha 1 acceptance: PENDING LINUX**

Project Lead accepted the functional qualification; final reconciliation and
separate supplemental checks establish complete authorized Windows coverage.
No blocking defect remains. The evidence retains native programmatic workflow
limits, separate run identities, Qt COM root-cause uncertainty, historical
baseline qualification and E9 preservation boundaries. Staging is authorized;
commit/push and Linux qualification remain unperformed. Stop after the staging
report for Project Lead authorization.
