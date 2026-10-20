# Bytefray 5.1 Pre-RC Remediation 03 — Spectator Launcher Reliability and Process Lifecycle

**Task ID:** P2 Remediation 03 (three launcher defects from Gemini Argon's independent review and the M2-5 integration reconciliation)

**Affected component:** Agent Designer's `SpectatorLaunchController` (`app/widgets/spectator_launch.py`)

**Remediation worktree:** `D:\Projects\BATTLE2-worktrees\p2-remediation-03-launcher`

**Remediation branch:** `v6-p2-remediation-03-launcher` (local, unpushed)

**Base commit:** `7ae2f9c2bdb3e65a353b2d12a44dbb525b70bd36` (`7ae2f9c`, accepted P1 Remediation 02)

**Result:** **PASS — All three launcher defects resolved and verified.**

- No missing-executable exception escapes any affected path.
- In-flight requests share a preparation only when their source, artifact root and expected identities are all equal.
- Every preparation `QProcess` is deleted exactly once, and late signals are inert.
- Supported Spectator launch, cached reuse and the Pygame fallback show no regression.
- Every affected regression passes; the full suite matches the baseline node for node.

Scope carry-forwards (frozen-build confirmation, Linux GUI CI, and an inherited test-isolation hazard in a pinned test) are listed in §F. None is a launcher defect.

**Independent review:** Gemini 4 Argon (High) through the Antigravity CLI, read-only, in an isolated clone with stdin closed and hard time limits.

| Round | Verdict | Findings |
|---|---|---|
| 1 | **APPROVE WITH NOTES** | one P2, four P3 |
| 2 | **APPROVE** | one P3 |
| 3 (test-only delta) | **APPROVE WITH NOTES** | one P3 |
| 4 (final test-only delta) | **APPROVE** | none |

Every actionable finding was corrected or explicitly dispositioned (§E).

Evidence is retained under the worktree's ignored `work/p2-remediation-03-20261020-01/` (`SHA256SUMS.txt` lists the artifacts and scripts).

---

## A. Baseline

| Item | Observation |
|---|---|
| Starting SHA | `7ae2f9c2bdb3e65a353b2d12a44dbb525b70bd36`, present locally |
| Ancestry | `0863846` (M2-5 ↔ identity reconciliation) and `a1aff90` (P1-01) are ancestors. `0863846..7ae2f9c` is exactly `a1aff90` (P1-01), `ff30490`, `f9b9da9` and `7ae2f9c` (P1-02) |
| P1-02 worktree | `D:\Projects\BATTLE2-worktrees\p1-remediation-02-wheel` at `7ae2f9c`, clean before and after this milestone |
| New worktree and branch | `git worktree add -b v6-p2-remediation-03-launcher … 7ae2f9c2bdb3e65a353b2d12a44dbb525b70bd36`; clean at creation |
| Other worktrees | The 25 pre-existing worktrees were listed, and none was used or modified. Protected checkouts (main `v6-research`, P1-01, P1-02, M2-5 reconciliation, `work/v6-m2-clean`, the Spectator clone) were snapshotted before and after (§G) |
| Version metadata | `pyproject.toml` `version = "5.0.0"`; `python -m battle_engine --version` → `Bytefray 5.0.0, Agent API v2, result schema v2, replay schema v4`. Unchanged |
| Environment | Windows 11 Pro 10.0.26120; repository `.venv` with CPython 3.13.14 and PySide6 6.11.2; `PYTHONPATH` bound to the worktree, because the venv's editable install points at the main checkout |

**Launcher behavior as found.** When a Simple or Advanced match completes, `AgentDesigner._on_proc_finished` calls `SpectatorLaunchController.prewarm()` inside a `try` that reports `OSError`, `ValueError` and `KeyError` as "Could not read canonical result". View Last Match goes through `AgentDesigner._open_result_replay`: the replay preflight runs, then `open_match()` takes over supported matches. The controller pins the request's ids, runs `bytefray spectator prepare` in a `QProcess`, launches Spectator on success, and otherwise warns and calls the Designer fallback (`_open_classic_result_replay`, a fresh preflight followed by the Pygame viewer). One preparation runs at a time; one more explicit request can wait.

**Coverage as found.** `tests/test_agent_designer_spectator.py` (10 `gui` tests, real prepare child) and `engine/tests/test_spectator_viewer_service.py` (14 test functions, 20 cases). None covered a missing exporter, request identity beyond `result_path`, process cleanup, or late signals. Baseline run: 10/10 passed (`runs/baseline-spectator-designer.log`).

## B. Root causes

### B.1 Defect A — missing frozen executable (P2)

In a frozen build, `build_prepare_command()` → `launchers.build_spectator_command()` → `_packaged_executable("bytefray")` raises `FileNotFoundError` when `bytefray.exe` is not beside the Designer. `SpectatorLaunchController._start` did not catch it:

| Path | Trigger | Effect at `7ae2f9c` |
|---|---|---|
| Background prewarm | A match completes in a frozen Designer without `bytefray.exe` | The exception reached Designer's result handler, which logged **"[Result] Could not read canonical result: Packaged executable not found…"**, blaming a valid match |
| View Last Match | The user clicks with the exporter missing | `FileNotFoundError` escaped `open_match` into the Qt slot. No fallback ran, and a background job that the click had just stopped was lost |
| Waiting request | A request queued behind a running preparation; the exporter disappears before it starts | The exception was raised from the `QProcess.finished` handler inside Qt's signal delivery, and the waiting request never fell back |

### B.2 Defect B — in-flight coalescing by `result_path` only (P2)

`open_match` treated any in-flight job with the same resolved `result_path` as the same work (`spectator_launch.py:112` at `7ae2f9c`), keeping that job's `artifact_root` and pinned ids and only setting `open_when_ready`. A `ResultReplayRequest` also carries `artifact_root`, `expected_match_id` and `expected_result_id`, and `_pinned()` fills missing ids from the result file *at the time of the click*. Consequences:

- A background job pinned to match X could be promoted for a click whose request pinned match Y at the same path (a run directory rewritten between completion and click). X's presentation then opened (the "stale-match launch" noted by Codex and recorded as R2 in the M2-5 reconciliation).
- A request with different expectations, including one that should fail verification, inherited the earlier job's validated expectations and never ran its own verification.
- The fallback received the earlier job's request rather than the user's.

`_pinned()` also used `or`, so an explicit but falsy expected id was replaced by the file's id.

### B.3 Defect C — QProcess lifecycle (P2)

`_stop_current` set `self._proc = None`, then called `kill()` and **`waitForFinished(2000)` on the GUI thread**. Qt delivers `finished` asynchronously (or inside that wait). The identity guard in `_finished` saw a non-current process and returned before `_complete` could call `deleteLater()`. Every superseded or shut-down preparation therefore left its `QProcess` alive until the controller itself was destroyed. Confirmed with real child processes: the stopped `QProcess` was never destroyed within 30 s (`runs/before-fix-final-tests-on-7ae2f9c.*`).

## C. Corrections

All product changes are in `app/widgets/spectator_launch.py`.

### C.1 Missing exporter (Defect A)

- `_start` wraps command construction in `try/except OSError` (which includes `FileNotFoundError`). Nothing is created or started on failure.
  - Background job: one log line, `[Spectator] Background preparation skipped: Spectator's match exporter is unavailable (Packaged executable not found: bytefray.exe. Checked: …)`. No dialog.
  - Explicit job: `_report_problem()` logs the problem on every use and shows it **once per session**, the same policy as an existing misconfigured `BYTEFRAY_SPECTATOR`. The fallback then runs with that job's own request.
- `_start` no longer raises, so `open_match`, `prewarm` and the completion handler cannot surface it. Designer's "Could not read canonical result" path is no longer reached for this cause.
- If the Pygame viewer is missing too, Designer's existing handler in `_open_result_replay` shows **"Replay Launch Failed"** with the missing `bytefray-replay-viewer` path. That is never a silent success, and nothing retries.

### C.2 Request identity (Defect B)

- **Equivalence rule.** `_Job.key = (result_path, artifact_root, expected_match_id, expected_result_id)`, with both paths canonicalized by `expanduser().resolve()` exactly as `preflight_result_replay` does. These are all of `ResultReplayRequest`'s fields. The other inputs to a preparation (data root, cache root, child environment) are the same for every job. The Spectator install only matters at launch, and `open_when_ready` is a promotion flag, not identity.
- **Sharing.** A request joins the job in flight only when the keys are equal. The job then adopts the new request and the install discovered for it, so launch and fallback serve the request just made, with no stale spelling or install.
- **One path.** Explicit requests and the queued request go through `_submit`. A different click stops a background-only job ("the click wins"), or waits next in line if an explicit preparation is running.
  - A newer click replaces the one waiting. That includes a click on the match already in flight, so only the newest choice is pending.
  - When nothing runs, a waiting request can only be left over from an interrupted `_complete`, and a new request drops it.
- `prewarm` starts nothing while a click waits.
- `_pinned()` keeps any id the caller supplied (`is None` checks), so a malformed expectation reaches verification and fails there.

### C.3 Process ownership (Defect C)

| Event | Handling |
|---|---|
| Normal completion or failed start | `_finished` / `_error(FailedToStart)` → `_complete`, which clears `_proc/_job/_install` and calls `deleteLater()` exactly once. A failed start is completed only by `_error` (Qt sends no `finished`); every other error is followed by `finished` |
| Supersession or shutdown | `_stop_current` clears `_proc/_job/_install` and disconnects the process's `readyReadStandardOutput`, `finished` and `errorOccurred` from every job. If it has already stopped, `deleteLater()`; otherwise `stateChanged(NotRunning) → deleteLater()` is connected and `kill()` is sent. **No `waitForFinished`** |
| Late signals | Disconnection stops them at the source, and the `proc is not self._proc` guards in `_read`, `_error` and `_finished` remain as a second net |
| Ownership | Each `QProcess` is created with the controller as parent, so even a child whose death is never reported is destroyed no later than the controller |

**Nested event loops.** `QMessageBox.warning` and the fallback spin nested event loops inside `_complete`, so a click or the window closing can arrive before `_complete` returns. After its dialogs, `_complete` leaves a waiting request to any preparation that started meanwhile (that preparation's completion serves it). Otherwise it submits the waiting request through `_submit`.

**Shutdown.** `shutdown()` (called from `AgentDesigner.closeEvent`) clears the waiting request, stops the current job, and sets `_closed`. `_start` and a new `_fall_back()` wrapper, used at all four fallback sites, do nothing afterwards, so a dialog still open at close cannot later open a viewer. Spectator windows already open are independent applications and stay open, as before.

**Early-exit check.** The early-exit check `QTimer.singleShot(EARLY_EXIT_MS, …)` now passes the controller as context, so it is dropped if the controller is destroyed first.

**No new UI.** No dialog, thread or dependency was added. The two remaining PySide6 stub complaints that `mypy` reports for this file are on unchanged lines; four were reported at `7ae2f9c`.

## D. Tests

### D.1 New tests

`tests/test_spectator_launch_controller.py` (new, `gui`, 27 tests) drives the controller with `_ScriptedProcess`. It is a real `QProcess` subclass that never spawns: each test decides when it starts, writes, exits, fails to start (synchronously, as Windows does), or reports its death after a kill. Overlap and late delivery happen by construction, not by timing.

Two further tests use real child processes and check the child's pid at the OS. They wait with `QProcess.waitForStarted`/`waitForFinished`, which deliver only that child's signals, never by pumping the application event loop (§D.4). No test in the module sleeps or pumps events; the only sleep is the child that stands in for a long export.

| Area | Tests |
|---|---|
| Missing exporter | background prewarm logs only and leaves no job; explicit open reports once, falls back every time with the pinned request, no process created; a waiting request falls back from the completion handler |
| Request identity | identical prewarm + click share one preparation; differing `artifact_root`, `expected_match_id`, `expected_result_id`, or an explicit empty `expected_result_id`, each get their own preparation with their own expectations on the command line; a replaced match is never opened from the earlier preparation even when the killed child prints a valid presentation; a shared preparation falls back with the request just made (as spelled); a separate one with its own; an unverifiable request is not vouched for by an earlier one and falls back itself; only the newest waiting click opens; re-clicking the match in flight drops an older waiting click; `~` is expanded like the preflight |
| Nested dialogs | a click during a failure dialog replaces the waiting click; a click waiting behind a newer preparation stays with it (queued once); closing during the dialog opens and starts nothing afterwards |
| Lifecycle | success, failure, crash (`Crashed` then `finished`) and failed start each complete once and delete their process once; supersession kills without `waitForFinished` and deletes only after the death is reported; late `readyRead`/`errorOccurred`/`finished`, and direct handler calls, never reach a job; shutdown stops, forgets the waiting click, and is idempotent under warnings-as-errors; real child superseded → killed and deleted; real child at shutdown → killed and deleted |

`tests/test_agent_designer_spectator.py` gained four Designer-level tests (real `AgentDesigner`, real matches). Frozen mode is simulated by patching `battle_engine.launchers.is_frozen_application` and `launchers.sys.executable`, so the real `_packaged_executable` raises its real message:

- background preparation without the exporter logs a skip and never blames the result;
- View Last Match without the exporter warns once and opens the Pygame viewer (twice for two clicks);
- with neither the exporter nor the replay viewer, Designer reports "Replay Launch Failed" for each click, with no crash and no loop;
- closing Designer kills a preparation child that only a kill can end, without blocking, and its pid is gone.

### D.2 Before/after

| Run | Tree | Result |
|---|---|---|
| Final round-1 test files (26 new + 10 existing) against unmodified code | `7ae2f9c` | **20 failed, 16 passed.** Every failure is on its target defect: unhandled `FileNotFoundError` ×4, misleading result message, no fallback from the completion handler, wrong request reused/fallen back ×8, `waitForFinished` called ×2, process never deleted ×4 (`runs/before-fix-final-tests-on-7ae2f9c.*`). The 6 passing new tests are guards for behavior that was already right |
| Round-2 test files against round 1 | `7830d5c` | **4 failed** (`~` expansion, stale waiting click, duplicate queueing, fallback after close), 38 passed (`runs/review-tests-on-7830d5c.*`) |
| Spectator controller + Designer Spectator modules | `040a709` | **41 passed**, 5 consecutive runs with capture disabled; no `QProcess: Destroyed while…`, Qt warnings or tracebacks (`runs/final_040a709_repeat_nocapture_0*`) |
| Evidence sandwich: timer and event left pending before the controller module | `040a709` / `5d55b90` | untouched / **fired** (§D.4) |

### D.3 Regression suites

All runs on Windows with `PYTHONPATH` bound to the tree under test and pytest's repo-local basetemp.

| Suite | `040a709` (final) | `7ae2f9c` (baseline) |
|---|---|---|
| Designer GUI, offscreen, all modules except the three below | **443 passed** | 412 passed. The 31 added are the new tests |
| Replay History browser, offscreen | 96 passed | 96 passed |
| Replay History qualification, offscreen | 36 passed | 36 passed |
| Client `gui` tests | 13 passed | 13 passed |
| M1-5 Designer, **native** Windows platform | 8 passed | 8 passed |
| Focused headless: `test_launchers`, `test_spectator_viewer_service`, `test_designer_workflows`, `test_designer_third_entrant_command`, `client/tests/test_spectator_export` (P1-01 exporter suite) | 222 passed, 4 skipped | covered by the full run. The skips are 2 POSIX-only cases and 2 that need the Windows symlink privilege, as recorded by P1-01 |
| Spectator repository suite: a fresh clone of `14089a7`, with this tree as production exporter and Godot 4.7.2 | **68 passed** | 68 passed at `7830d5c` |
| Full headless suite (`python -m pytest`, pytest.ini defaults, both trees concurrently in detached helper worktrees) | **8,995 passed, 86 failed, 3 errors, 36 skipped** (1:29:19) | 8,995 passed, 86 failed, 3 errors, 36 skipped (1:31:04) |

The GUI split is the established one: a single combined offscreen run hits a known pre-existing Replay History crash, and M1-5 needs the native platform. The intermediate candidate `7830d5c` gave 437 passed and 1 failed in the first part. That failure is the inherited isolation hazard in §D.4; the other parts were identical.

Per-node JUnit comparison (`full/compare_full.txt`):

- **`040a709` vs `7ae2f9c`:** 9,120 common nodes; **0 outcome changes, 0 new failures, 0 added or removed.** The headless suite does not collect the root `tests/` GUI modules, and no headless test imports `app.widgets.spectator_launch`, so this is the expected result.
- **`040a709` vs P1-02's `ff30490` run** (the run that carried the documented baseline): 0 outcome changes. The 89 failing nodes (86 failures, 3 errors) are **identical** to the documented inherited 89: E9/E8 freeze and integrity guards, research-Ruleset selectability assertions, and the E9 `outside_repository` case under the repo-local basetemp. None was suppressed. The 6 added and 5 removed nodes are P1-02's own `f9b9da9` changes to `test_check_wheel`, and all of them pass.
- The 14 documentation-consuming modules identified by the reconciliation gave **488 passed, 1 skipped** with this report present, the same result P1-02 recorded.

**Interrupted runs.** The first pair of full-suite runs (at `7830d5c` and `7ae2f9c`) was killed by an external event at 02:00:16, at 86% complete, together with an unrelated repeat run in this worktree. All four processes ended in the same second with exit code 1 and no output. They shared only the interpreter `D:\Projects\BATTLE2\.venv\Scripts\python.exe`; VS Code's language servers on a different interpreter survived. The venv and the main checkout were unchanged (nothing modified after 01:55). The logs are kept under `full/interrupted-0200/`, and both suites were rerun from the start on the final tree and the baseline.

### D.4 Inherited test-isolation hazard found and contained

The first candidate GUI run failed `test_v5_alpha1_phase4_tournament_results.py::test_designer_runs_a_real_tournament_and_opens_its_results` deterministically: "did not finish within 120 seconds", in 0.14 s.

- **Mechanism.** Instrumentation showed `QEventLoop.exec()` returning `-1` at once, and a `Quit` event reaching `QApplication` inside a later test's `processEvents()`.
- **Origin.** `tests/test_linux_designer_smoke.py` closes its window at 50 ms and arms `QTimer.singleShot(60, application.quit)`. Closing the last window *posts* a `Quit`, and the explicit quit can overtake it, so `exec()` returns with that `Quit` still queued. The next test that pumps events outside `exec()` delivers it, after which every `QEventLoop.exec()` in the session returns immediately.
- **Predates this branch.** On unmodified `7ae2f9c`, the smoke test followed by the existing `test_view_last_match_never_blocks_the_gui_thread` and the tournament test fails the same way (`runs/hazard-on-7ae2f9c-*`). Default alphabetical order happened to place no event-pumping module between the smoke test and the tournament test until the new controller module.
- **Containment, in three steps.**
  1. A fix in the smoke test itself (stop the safety timer and `removePostedEvents(application, QEvent.Type.Quit)` after `exec()`) was verified and approved by Argon in round 2. It was then reverted (`1c61f91` → `927c6d1`), because that file is pinned by the M2-5 qualified source manifest and stays byte-for-byte unchanged.
  2. The replacement guard in `927c6d1` removed a queued `Quit` before the module pumped events. Argon's round 3 showed it was not enough: when the window's `Quit` ends `exec()` first, the residue is the smoke test's still-armed 60 ms quit timer, which any `processEvents()` fires.
  3. Since `040a709`, the module never pumps the application event loop. Its real-process tests wait with `waitForStarted`/`waitForFinished`, and its scripted tests deliver signals directly and flush only `DeferredDelete`.
- **Verification of the containment.** An evidence-only sandwich (`scripts/diag/test_foreign_events_untouched.py`) arms a 5 ms timer and posts an event before the module, then asserts both untouched after it. It passes at `040a709` and fails at `5d55b90` ("a later module fired a timer an earlier test left armed"), so the module now cannot set off either form of the hazard. The smoke-test fix is recommended as a separately authorized change (§F).

### D.5 Windows GUI smoke (real application)

`scripts/gui_smoke.py` drives a real `AgentDesigner` on the **native** Windows Qt platform, with disposable data, through Simple-tab Run Match with the V6 starters (Window Scout vs Watchful Keeper, Active Sensing (Alpha)). It uses the real `prepare` child, the real exported Spectator 14089a7 build (copied to a folder whose path contains a space) and the real Pygame viewer. It calls Designer's slots directly instead of clicking. Dialogs are recorded rather than shown, and every viewer it opens is closed again.

| Scenario (`040a709`, `final_040a709_gui_smoke_report.json`) | Observed |
|---|---|
| 1. A supported completed Alpha1 match launches Spectator | The 200-tick match completed and background preparation started at once. View Last Match launched the real Spectator 13.2 s after the click (a first export, with the full suites loading the machine). Spectator was still running after 4 s. The presentation verified against the current exporter, and its `match_id` equals the result's. No dialog; Pygame not used; largest event-loop gap during the wait 0.19 s |
| 2. Cached reopening | 0.66 s to launch, same presentation, "reused a verified presentation" logged, no dialog |
| 3. Spectator disabled (`BYTEFRAY_SPECTATOR=off`) | The real Pygame viewer started (`python -m battle_client.cli --replay … --renderer pygame`) and was still running after 4 s. No Spectator, no dialog |
| 4. Missing executables do not crash Designer | Exporter missing (frozen simulation, viewer present): one "Spectator Unavailable" warning naming `bytefray.exe` and both checked paths; the real Pygame viewer opened; controller idle. Background preparation: one skip log line, no dialog. Exporter **and** replay viewer missing: one "Replay Launch Failed" naming `bytefray-replay-viewer.exe`; nothing launched; the Spectator warning not repeated; window still open |
| 5. Cancelling preparation returns the GUI to a usable state | (a) A 600-tick match's background export was running. A click for another match returned in 13 ms; the old child was killed (OS pid gone) and its `QProcess` deleted; the clicked match, not the long one, opened in Spectator; largest event-loop gap 0.039 s. (b) The window was closed during an export: `close()` returned in 6 ms, the controller was idle, the `QProcess` was deleted, and the child's pid was gone |

All viewer windows opened by the smoke were closed again (`unclosed_viewers: 0`).

An earlier smoke on `1c61f91` gave the same outcomes, plus one "Spectator exited immediately (exit code 1)" warning. The driver itself had terminated the scenario-2 Spectator 2 s after launch, inside the product's 2.5 s early-exit window, so that warning was correct behavior. The driver now waits 4 s.

### D.6 Static checks

- `ruff check .`: all checks passed.
- `mypy engine/src/battle_engine`: 107 source files clean. `mypy client/src/battle_client`: 20 source files clean.
- `mypy app/widgets/spectator_launch.py` (not a project mypy target): 2 errors at final, both PySide6 stub mismatches for `bytes(QByteArray)` on unchanged lines. There were 4 at `7ae2f9c`.
- The root `tests/` GUI modules are not mypy targets.
- `tools/release_compatibility.py --check docs/releases/BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json`: passed.
- `git diff --check`: clean.

## E. Independent review

Gemini 4 Argon (High), Antigravity CLI `agy`, run as `--mode plan --sandbox --print-timeout …` inside an outer `timeout`, with **stdin from `/dev/null`**. It ran in a clone of this branch with the push URL disabled, so the earlier stdin-EOF stall could not recur. Tool permissions were not auto-approved; the reviewer read files only, and the diff was provided as a file in the clone. Briefs and reports are under `review/`.

| Round | Scope | Duration | Verdict | Findings and disposition |
|---|---|---|---|---|
| attempt 0 | `7830d5c` | 20 s | no output | The reviewer tried a terminal command, which headless mode denied. Re-run with file-only instructions; this is not a finding |
| 1 | `7ae2f9c..7830d5c` | 12 min | APPROVE WITH NOTES | **P2** nested-event-loop re-entrancy in `_complete` (stale waiting click run after a newer one; a waiting request taken from a newer preparation; fallback after shutdown) → corrected in `1c61f91`. **P3** close test did not prove a running child was killed → corrected. **P3** missing re-entrancy and falsy-id tests → added. **P3** unparent the dying `QProcess` so early parent destruction cannot run `~QProcess` before the kill is reported → **declined**: a parentless `QProcess` could outlive the `QApplication` at interpreter teardown; with the parent kept, the worst case is Qt's own reap of an already-killed child (§F). **P3** `expanduser` → corrected |
| 2 | `7830d5c..1c61f91` | 5.6 min | APPROVE | Confirmed findings 1, 2, 3, 5 resolved with no regression; **accepted** the finding-4 disposition; approved the smoke-test fix (later withdrawn for the manifest pin, §D.4). **P3 (unconfirmed)**: on POSIX a `QProcess` may still be `Starting` right after `start()` → corrected in `5d55b90` |
| 3 | `1c61f91..5d55b90` | 13.5 min | APPROVE WITH NOTES | Confirmed the pinned smoke test is restored and the round-2 P3 correction is right; the harness guard hides nothing the module should test. **P3**: the guard removes a queued `Quit` but not the smoke test's armed 60 ms quit timer, which this module's `processEvents()` could fire (when the window's `Quit` ends `exec()` first, e.g. without Windows timer coalescing). Confirmed by the evidence sandwich at `5d55b90`. Corrected in `040a709` without running `exec()` in teardown (the suggested drain would also run every other pending timer and handler): the module no longer pumps the event loop at all (§D.4) |
| 4 | `5d55b90..040a709` | 2 min | APPROVE | No findings. Confirmed on Windows and POSIX that `waitForStarted`/`waitForFinished` and the `DeferredDelete`-only flush dispatch no timer or queued event left by another test. Also confirmed that the rewritten real tests still prove supersession kills and deletes the old child, that the new job completes through `_finished` → `_complete`, and that shutdown kills its child |

Codex was not used for this milestone.

## F. Remaining limitations

1. **No user-facing cancel control.** Designer has never had a cancel button for Spectator preparation, and none was added (no new features). Cancellation happens by supersession (a click for another match stops a background-only preparation) and by closing the window. Progress is logged, never shown in a dialog, so no progress dialog can get stuck. An *explicit* preparation in flight is not stopped by a click for another match: the later click waits, and only the newest waiting click is kept (spec §7).
2. **Early parent destruction (review finding 4: declined, and the reviewer accepted the disposition).** If the controller is destroyed before Qt reports a killed child's exit, Qt's `~QProcess` prints a warning and waits for the already-killed child. In Designer that can only happen at application exit, after `closeEvent` has sent the kill.
3. **Process races.** No unresolved race is known. Within the controller, a click or close delivered during any nested dialog is handled (§C.3) and tested. Races involving the Spectator executable itself (its own startup and the 2.5 s early-exit check) are unchanged. A Spectator closed with a nonzero code inside 2.5 s is reported as "exited immediately"; the smoke driver triggered this once by terminating Spectator at 2 s, which is the intended behavior.
4. **Frozen-executable coverage is simulated.** The missing-exporter paths were exercised in source mode, by making `launchers` believe it is frozen in a folder without its companions; the real `_packaged_executable` raised the real error. No PyInstaller build was made, and the frozen Designer was not requalified. That belongs to Packaged Application Qualification.
5. **GUI qualification.** The automated GUI tests ran offscreen and, for M1-5 and the smoke, on the native Windows platform. The smoke used the real Designer, Spectator and Pygame applications but called slots directly; no human clicked through the application. Linux was not run for this remediation, and CI's `linux-gui-smoke` workflow has not been observed, because nothing was pushed.
6. **Inherited test-isolation hazard (§D.4).** It remains in the pinned `tests/test_linux_designer_smoke.py`. The new module cannot trigger it, and the default (alphabetical) ordering places no other event-pumping test between the smoke test and a `QEventLoop.exec()` test. However, a custom ordering that does (for example, running the pre-existing `test_view_last_match_never_blocks_the_gui_thread` after the smoke test) still trips it, exactly as at `7ae2f9c`. The smoke-test fix (stop its safety timer and remove its posted `Quit` after `exec()`) is ready for a separately authorized change to that pinned file.
7. **Unchanged by design:** first-time export performance (`SensingCursor.current_view`), presentation generation, cache format, and Spectator scope (two-agent Active Sensing (Alpha); Broadcast and Agent A perspectives; Classic and three-agent matches keep the Pygame viewer).
8. **Previously accepted 5.1 limitations stand:** E9 **LOCKED**; Requirement C **NOT ESTABLISHED**; M2-6 deferred to 5.2; native Xorg unqualified; sensing demonstrations source-only; Linux wheel coverage WSL2 only; CI `build-linux-wheel` not observed. The 89 inherited full-suite failures are unchanged (§D.3).

## G. Git state

Branch `v6-p2-remediation-03-launcher` in `D:\Projects\BATTLE2-worktrees\p2-remediation-03-launcher`, local commits on `7ae2f9c`:

| Commit | Content |
|---|---|
| `7830d5c` | `fix(designer): make the Spectator launcher's fallback, request identity and process lifecycle reliable` (controller, new controller tests, Designer tests) |
| `1c61f91` | `fix(designer): settle Spectator requests made while a completion's dialog is open` (review round 1 corrections; also the smoke-test isolation fix that `927c6d1` withdraws) |
| `927c6d1` | `test(designer): keep the launcher tests clear of a Quit left by an earlier test` (restores the pinned smoke test byte-for-byte; a Quit-removal guard that `040a709` replaces) |
| `5d55b90` | `test(designer): wait for the preparation to run before reading its pid` (review round 2 P3) |
| `040a709` | `test(designer): wait on the real preparation children instead of pumping events` (review round 3 P3; final code state) |
| Branch head | `docs(release): add the Pre-RC Remediation 03 report` (this file only); its SHA is reported in the hand-off |

Changed files `7ae2f9c..HEAD`: `app/widgets/spectator_launch.py`, `tests/test_agent_designer_spectator.py`, `tests/test_spectator_launch_controller.py` (new), `docs/releases/5_1_PRE_RC_REMEDIATION_03.md` (new).

Protected state:

| Protected item | Verification |
|---|---|
| P1-01 Spectator export/replacement logic, P1-02 wheel work | Not touched; no file under `engine/src`, `client/src`, `tools`, `pyproject.toml` or `MANIFEST.in` changed |
| M2-5 qualified source manifest (1,249 pins) | 23 inherited mismatches at `7ae2f9c` and at `040a709`; **none new** (`m2-5-source-manifest-delta.txt`). The pinned `tests/test_linux_designer_smoke.py` differed only at the intermediate `1c61f91` and is byte-identical to `7ae2f9c` again |
| E9 | No `engine/src` file changed; E9 remains **LOCKED** |
| Spectator repository and Godot source | `14089a7`, clean; read only (a separate clone ran its tests; the exported build was copied for the smoke) |
| Presentation contracts, replay/trace/result schemas, ruleset and Agent API identities, starters, gameplay, historical evidence, component versioning | Not touched |
| Protected checkouts | Main `v6-research` (`2fc3c82`), P1-02 (`7ae2f9c`), P1-01 (`a1aff90`), M2-5 reconciliation (`0863846`), `work/v6-m2-clean` (`10c3530`) and the Spectator clone (`14089a7`): HEAD, branch and working-tree status identical before and after (`protected-before.txt`, `protected-after.txt`). Shared repository refs are unchanged apart from this branch: 24 `refs/codex/*`, 187 total |

The worktree is clean after the report commit (`git status --porcelain` empty; evidence is under the ignored `work/`). Nothing was pushed, merged or tagged. The branch has no upstream, and no release branch, tag or version bump was created. These are disposable:

- the detached helper worktrees `p2-remediation-03-full-040a709` and `p2-remediation-03-full-7ae2f9c`;
- the directory `D:\Projects\BATTLE2-worktrees\p2-remediation-03-full-7830d5c`, already unregistered from Git, whose deletion failed on a locked file after the 02:00 interruption;
- the review clone and the Spectator test clone in the session scratchpad.

The temporary worktrees used for the before/after runs were removed.

Work stops here. Bytefray 5.1 Alpha Packaged Application Qualification and Release Candidate Preparation were not started and require separate authorization.
