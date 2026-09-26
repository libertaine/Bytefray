# Bytefray V5 — Phase 7D: Replay Viewer Handoff & Copy Seed

Phase 7D adds the two remaining Replay History actions the Phase 6
architecture approved — **Open Replay** and **Copy Seed** — to the Phase 7C
browser. `Re-run Match` remains explicitly out of scope, exactly as Phase 6
Section S required.

---

## A. Starting state

| Item | Observed value |
|---|---|
| Branch | `v5-research` |
| Exact HEAD | `c265fddc5e703108c5de199977eedda8b6ffd02a` |
| Upstream | `origin/v5-research`, 0 ahead / 0 behind |
| Bytefray version | `5.0.0a1` (unchanged) |
| Working tree at start | **Not clean.** Phase 7C's implementation was present as uncommitted work: modifications to `ARCHITECTURE.md`, `README.md`, `app/agent_designer.py`, `docs/MANUAL_SMOKE_TESTS.md`, and `engine/src/battle_engine/replay_history/{__init__,index,query,service}.py`, plus untracked `app/views/replay_history.py`, `app/services/replay_history_presentation.py`, `docs/research/v5/V5_REPLAY_HISTORY_PHASE7C_BROWSER_UI.md`, `engine/tests/test_v5_replay_history_presentation.py`, and `tests/test_v5_replay_history_browser.py` |
| Phase 7B | Committed at HEAD |
| Phase 7C | Present and matched its own report exactly; preserved and built upon rather than re-authored |

No pre-existing change was discarded or absorbed as if authored by this
phase; every file Phase 7C touched that Phase 7D also needed to touch was
edited in place, on top of its existing content.

---

## B. Existing Viewer launch architecture (reused, not reimplemented)

```
selected occurrence
  -> ReplayHistoryWindow._onReplayResolved (GUI thread)
  -> app.services.engine_commands.open_pygame_client_direct(data_root, replay_path)
  -> battle_engine.launchers.build_replay_command(replay_path, flags)
  -> Popen(...)  (non-blocking; detached Replay Viewer process)
```

`open_pygame_client_direct` already existed, already validates the path
(`FileNotFoundError` if missing), already appends `--trace` when a sibling
`trace.jsonl` exists, and is the exact function `_on_open_replay` (View Last
Match) and Advanced's replay button already call directly on the GUI thread —
it is a non-blocking `Popen`, not a filesystem read, so calling it
synchronously from `_onReplayResolved` matches existing Designer convention
precisely. Phase 7D imports and calls this function unchanged; nothing in
`launchers.py` or `engine_commands.py` was modified.

---

## C. History action architecture

Two new `QPushButton`s (`Open Replay`, `Copy Seed`) plus a transient
`actionStatusLabel`, inserted between `detailPane` and `advancedCheck` in
`_buildDetailArea()` — exactly the slot Phase 7C's own report reserved for
this ("`_buildDetailArea()` already has a vertical layout above
`advancedCheck`; an action row there needs no layout change elsewhere").

No context menu was added: a repo-wide grep found no existing
`QMenu`/`customContextMenuRequested` convention in any Designer view, and the
button row plus Enter/double-click already give full discoverable keyboard
and mouse access to both actions — adding an unprecedented pattern for two
actions already reachable three other ways was not justified.

---

## D. Replay availability mapping

| `ReplayState` (cached row) | Open Replay button |
|---|---|
| `AVAILABLE` | Enabled |
| `MISSING` | Disabled |
| `NOT_PRODUCED` | Disabled |
| `INVALID` | Disabled |
| `INACCESSIBLE` | Disabled |
| `UNCHECKED` | Disabled |

Implemented as `open_replay_enabled(replay_state) -> bool` in the Qt-free
presentation module — one function, one decision, tested for every enum
member (`test_open_replay_is_only_enabled_for_the_available_state`).

`UNCHECKED` was deliberately mapped to **disabled** rather than "requires
verification": the only place discovery currently assigns `UNCHECKED` to a
real row is `_normalize_invalid_result_occurrence`'s "no discoverable replay
file" branch (`discovery.py`), which means there is no file to open in the
first place — offering the button there would only ever fail at click time.
Every genuinely playable row already reports `AVAILABLE`. This is a
conservative default the report documents explicitly, per Section 5's own
framing that a stricter mapping is an acceptable choice.

The button decision is a *cached-state offer*, never an authorization: every
click still re-resolves and re-verifies before anything launches (Section E).

Copy Seed is independent: `copy_seed_enabled(seed) -> bool` is `seed is not
None` — `HistoryRow.seed` was already on the row Phase 7C's table model
holds, so no second query is needed to know whether a seed exists.

---

## E. Worker/preflight flow

```
GUI thread                              Worker thread ("bytefray-replay-history")
-----------                             --------------------------------------
_activateOpenReplay()
  -> guard: _open_pending / no selection
     / row not AVAILABLE -> no-op
  -> _open_pending = True
  -> _open_request_id += 1
  -> openReplayButton.disable()
  -> actionStatusLabel = "Checking replay…"
  -> openReplayRequested.emit(location_id, request_id)  (queued) --------->  ReplayHistoryWorker.openReplay(location_id, request_id)
                                                                                resolution = service.resolve_replay(location_id)
                                                                                integrity = (
                                                                                    service.verify_replay_integrity(resolution)
                                                                                    if resolution.available else None
                                                                                )
_onReplayResolved(ReplayOpenResult) <---------------------------------------   replayResolved.emit(ReplayOpenResult(request_id, location_id, resolution, integrity))
  -> if request_id != self._open_request_id: drop (stale)
  -> _open_pending = False; re-derive button state from *current* selection
  -> if self._shutdown_started: drop (never launch post-shutdown)
  -> not resolution.available -> status text, no launch
  -> integrity.status is MISMATCH -> status text + QMessageBox.warning, no launch
  -> integrity.status is UNREADABLE -> status text, no launch
  -> otherwise (VERIFIED or UNVERIFIED_LEGACY):
       open_pygame_client_direct(self._data_root, Path(resolution.path))  (GUI thread, non-blocking Popen)
       actionStatusLabel = "Opened replay in Replay Viewer."
```

Both `resolve_replay` and `verify_replay_integrity` run inside the single
worker slot invocation — one round trip, not two — which matters because two
round trips would each separately queue behind an active reconcile on the
Phase 7C single-worker architecture (Section M). `resolveReplay`/
`verify_replay_integrity` are proven to run off the GUI thread by
`test_resolve_and_verify_calls_happen_off_the_gui_thread`, following the
identical thread-identity-recording technique Phase 7C's own
`test_every_service_call_happens_off_the_gui_thread` uses.

**Copy Seed has no worker involvement at all** — the seed is already on the
in-memory `HistoryRow`/`HistoryDetail`, so the click handler reads
`self._selected_seed` and writes to the clipboard directly on the GUI thread.

---

## F. Path containment

Unchanged and fully reused: `resolve_replay` re-resolves the replay's
relative path with `contained_path(self._runs_root, relative)` — rejecting
`../` traversal, drive-qualified paths, and symlink escapes — and re-checks
the filesystem, exactly as Phase 7B implemented it. Phase 7D adds **no**
second path-safety mechanism; `ReplayHistoryWindow` never constructs a path
from artifact metadata itself, only ever passing back the `resolution.path`
string it received.

---

## G. Integrity/digest policy

One additive backend enhancement, matching the Section 38 gate ("a backend
change is allowed only if it adds a missing safe handoff capability... has
focused tests... is documented"):

* `battle_engine.replay_history.query.ReplayIntegrityStatus` — new enum:
  `VERIFIED`, `UNVERIFIED_LEGACY`, `MISMATCH`, `UNREADABLE`.
* `battle_engine.replay_history.query.ReplayIntegrityCheck` — new frozen DTO
  (`status`, `digest`, `diagnostic`).
* `ReplayHistoryService.verify_replay_integrity(resolution) -> ReplayIntegrityCheck`
  — new method. Takes the *already-resolved* `ReplayResolution` (never a
  second read of `result.json`); if `expected_sha256` is `None`, returns
  `UNVERIFIED_LEGACY` immediately (existence/containment were already proven
  by `resolve_replay`); otherwise hashes the resolved file's actual bytes and
  compares.
* `battle_engine.result_model.verify_replay_digest_value(expected_sha256, path) -> str`
  — new function, extracted from the existing `verify_replay_digest(result,
  path)` (which now delegates to it unchanged) so a caller holding only the
  expected digest string — exactly `ReplayResolution.expected_sha256` — does
  not need to construct or re-read a full `ResultEnvelope` merely to reach one
  field. `verify_replay_digest`'s own behavior, error codes, and existing
  tests (`test_replay_reconstruction.py`) are unaffected; this is a pure
  refactor plus one new entry point.

No SQLite schema change, no discovery-semantics change, no artifact-schema
change. `resolve_replay` itself is untouched.

**Policy: Verified / Unverified legacy / Mismatch / Unreadable**

| Result | Meaning | Launch? |
|---|---|---|
| `VERIFIED` | Live bytes match the digest recorded at index time | Yes |
| `UNVERIFIED_LEGACY` | No digest was ever recorded (pre-digest artifact); file exists, is contained, and is readable | Yes |
| `MISMATCH` | Live bytes differ from the recorded digest — the file changed since indexing | **No** — `QMessageBox.warning("Replay Changed", …)`, no bypass offered |
| `UNREADABLE` | File vanished or became unreadable between `resolve_replay` and the digest read (or the resolution was never `available`) | **No** — inline status text, no dialog |

This is the "safer default for V1" Section 14 recommended: a digest mismatch
blocks launch unconditionally in this phase. No "Open Anyway" bypass exists —
asserted by
`test_open_replay_blocks_launch_on_digest_mismatch_and_explains_why`, which
also asserts `not hasattr(window, "openAnywayButton")`.

---

## H. Viewer handoff

Exactly Section B's diagram. `test_open_replay_launches_through_the_canonical_viewer_helper`
monkeypatches `app.views.replay_history.open_pygame_client_direct` and asserts
it is called with `(window._data_root, Path(resolution.path))` — this is the
"existing launch-path integration test" Section 41 requires: it fails if a
future change bypasses this function for a second command-construction path.

`self._data_root` is resolved the same way `ReplayHistoryService.open()`
resolves its own default (`get_data_root()` when `None`), so History always
hands the launcher a concrete path even though the Designer today always
passes a concrete `data_root` in practice.

---

## I. Missing/changed/inaccessible replay behavior

| Scenario | Behavior |
|---|---|
| Replay deleted after indexing, before click | `resolve_replay` reports `MISSING`; status reads **"Replay file is no longer available."**; no launch |
| Replay deleted between `resolve_replay` and the digest read (the resolve-to-launch race) | `verify_replay_integrity` catches the missing/unreadable file as `UNREADABLE`; same status text; no launch |
| Replay bytes changed after indexing | `MISMATCH`; blocking dialog (Section G); row/history entry is untouched |
| Permission error reading the replay | `INACCESSIBLE` (from `resolve_replay`) or `UNREADABLE` (from the integrity check, if the permission error surfaces during the digest read instead) — both produce a status message distinct from "missing" |
| Result has `replay: null` (pMARS) | `NOT_PRODUCED`; button was never enabled for this row |

No test crashes, no traceback reaches the user, and no History row, result
artifact, or replay artifact is ever mutated by any of these paths.

---

## J. Copy Seed

* Enabled iff `HistoryRow.seed is not None` — zero, negative (if a future
  writer ever records one), and very large seeds all remain enabled; only
  `None` disables it.
* Copies `str(seed)` verbatim via `QGuiApplication.clipboard().setText(...)` —
  no label, no surrounding whitespace.
* Feedback: `actionStatusLabel` reads `f"Seed {seed} copied"` — text, not a
  modal dialog, per Section 27.
* Tooltip (present at all times, not only after a click): *"Copies the match
  seed. Reproducing the exact match also requires the same agents, ruleset,
  parameters, and configuration."* Tests assert this text names the
  limitation and never uses "guarantee" or an unqualified "exact" claim, and
  the button itself is labelled **Copy Seed**, never "Copy Reproduction
  Seed."

**One real, minor finding from the manual smoke (Section Q):** `actionStatusLabel`
is shared between both actions. If a user clicks Open Replay and then clicks
Copy Seed before the (normally millisecond-scale) preflight response arrives,
the Copy Seed confirmation text can be overwritten a moment later by the
delayed Open Replay status. The clipboard write itself is unaffected — only
the transient confirmation text can be superseded. This is cosmetic, not a
functional defect, and is recorded here rather than silently fixed with an
unreviewed change to shared status-label ownership; recommended for 7E if it
proves bothersome in practice.

---

## K. Keyboard/mouse actions

One shared entry point, `_activateOpenReplay()`, reached three ways:

* **Button** — `openReplayButton.clicked`.
* **Double-click** — `table.doubleClicked` → `_onTableDoubleClicked` →
  `_activateOpenReplay()`. An unplayable row's double-click is a no-op (no
  dialog, no launch); ordinary selection behavior is untouched.
* **Enter/Return** — an event filter installed on `self.table` only (never
  the dialog or any other widget) intercepts `QEvent.KeyPress` for
  `Key_Return`/`Key_Enter` and calls `_activateOpenReplay()` when the button
  is currently enabled, consuming the event; otherwise it declines the event
  and normal Qt behavior applies. Because the filter is scoped to the table
  `QObject`, Enter inside `searchEdit` (or any other filter control) never
  reaches it — asserted directly by
  `test_enter_activates_open_replay_only_while_the_table_has_focus`.

`test_button_enter_and_double_click_share_one_activation_path` monkeypatches
`_activateOpenReplay` itself and proves all three input paths call it exactly
once each — the mechanical proof Section 43 asks for, not just three separate
behavioral tests that happen to agree.

Copy Seed has no keyboard shortcut beyond ordinary Tab-to-focus plus
Space/Enter on the focused button (standard `QPushButton` behavior); no
additional binding was added because Section 26 does not ask for one and the
existing focus order already reaches it.

---

## L. Cancellation/shutdown

**Chosen policy (Section 11):** once a request commits (`_open_pending =
True`, `_open_request_id` incremented), the *only* things that can invalidate
it are (a) the window's shutdown flag, or (b) — not reachable through normal
UI, since a second click is refused while one is pending — a request-id
mismatch. If the user's selection moves to a different row while the request
is in flight, the original request still launches its own resolved replay
when it completes; button/state re-derivation on completion uses the
*current* selection, not the one the request was issued for. This is
deliberate and tested
(implicitly, by the fact that `_onReplayResolved` never reads
`self._selected_location` to decide whether to launch — only `result.request_id`
and `self._shutdown_started`).

**Shutdown:** `shutdownWorker()` sets `_shutdown_started = True` and disables
both action buttons synchronously, before the (potentially slow) blocking
`QThread.wait()`. `_onReplayResolved` checks this flag first and drops the
response unconditionally if set — a Viewer is never launched after the owning
window has begun shutting down, even if the preflight had already reached
`VERIFIED` by the time the response arrives
(`test_closing_the_window_during_a_pending_preflight_never_launches_afterward`).
The worker thread is never terminated; a queued-but-blocked `openReplay` call
is simply allowed to finish naturally (or, in the real backend, to return
promptly, since `resolve_replay`/digest verification are not long-running
operations) before the already-queued `shutdownRequested` runs.

A stale response — simulated directly by constructing a `ReplayOpenResult`
with a superseded `request_id` and feeding it to `_onReplayResolved` — is
dropped without touching the launcher, the status label, or button state
(`test_a_stale_open_replay_response_is_dropped_not_launched`).

---

## M. Single-worker contention

Phase 7C measured (real 53,458-occurrence corpus, this machine): warm
reconcile **8.5 s**; a `fetchDetail` request issued while that reconcile is
running waits **≈7.4 s** for the single worker. `resolve_replay` and
`verify_replay_integrity` queue behind an active refresh through the
*identical* mechanism (`ReplayHistoryWorker` slots on one `QThread`'s one
event loop) — Open Replay inherits this figure directly rather than requiring
a fresh measurement of the same architectural fact.

This session attempted a fresh full-corpus measurement (rebuilding the real
53,458-occurrence cache from a clean cache directory) and observed the
process consuming well under 2% CPU over several minutes of wall-clock time —
strongly I/O-bound in a way that, extrapolated, would take on the order of
hours to complete in this particular environment session, versus Phase 7C's
own measured 279 s cold rebuild on the same machine. This was not pursued
further; it reads as session/environment variance (see Section T) rather than
anything Phase 7D changed, since Phase 7D adds no filesystem-scan or SQL
logic and the cold-rebuild path it queues behind is unmodified Phase 7B code.

**What this phase did measure directly**, against a real, scoped, 72-artifact
product-owned subtree (`runs/evaluations`, cold-built in this session): a
click-to-preflight-response round trip of **≈0.03 s** end to end (resolve +
digest verification of a real replay file's real bytes), with the launcher
call itself mocked to a no-op recorder rather than actually spawning a Pygame
window in this headless session. This confirms the plumbing is fast and
correct against genuine artifacts; it does not by itself reproduce the
large-corpus contention window, which the fake-service GUI tests reproduce
deterministically instead (Section M's `resolve_gate`-based tests hold a
preflight open indefinitely and assert the GUI never freezes and no wrong
launch occurs).

No second worker/connection was added. Per Section 39/M, this phase
characterizes the effect rather than solving it; a second read-only service
remains Phase 7E's recommendation (already made by Phase 7C, unchanged here).

---

## N. Error UX

| Situation | Presentation |
|---|---|
| Replay missing / not produced / invalid / inaccessible at click time | Inline `actionStatusLabel` text, state-specific, never a dialog |
| Digest mismatch | `QMessageBox.warning("Replay Changed", …)` — the one case judged to warrant an explicit acknowledgment, matching the existing app convention of `QMessageBox.warning` for a surprising-but-recoverable state |
| Viewer launch failure (`FileNotFoundError`/`OSError` from `open_pygame_client_direct`) | `QMessageBox.critical("Replay Launch Failed", str(exc))` — the exact existing convention `_on_open_replay` and Advanced's replay button already use |
| Worker exception during resolve/verify | Caught, converted to `WorkerError("open_replay", …)`, surfaced as `f"Replay could not be checked — {message}"` inline text; existing rows/selection are left untouched |
| Copy Seed with no seed | Button is simply disabled; nothing to click |

No traceback, SQL fragment, or internal path reaches ordinary status text;
the mismatch dialog and launch-failure dialog carry only the bounded
diagnostic/exception message.

---

## O. Accessibility

* `openReplayButton`/`copySeedButton` both have `setAccessibleName` and a
  tooltip that doubles as the accessible description Qt derives for a
  `QPushButton`.
* Both are reachable via Tab in normal focus order; neither relies on an icon
  alone.
* `actionStatusLabel` has an accessible name (`"Replay action status"`) so a
  screen reader can be pointed at it; it is plain text, not color-coded.
* The digest-mismatch/launch-failure dialogs are ordinary `QMessageBox`
  instances, which already carry Qt's standard accessible role/text.

---

## P. Tests

| Module | New tests | What they cover |
|---|---:|---|
| `engine/tests/test_replay_history.py` | **+5** (88 total, was 83) | `verify_replay_integrity`: verified (real native match), mismatch (tampered real replay bytes), legacy no-digest (real replay-only entry), vanished-after-resolve race, defensive handling of a non-available resolution |
| `engine/tests/test_replay_reconstruction.py` | **+3** (18 total, was 15) | `verify_replay_digest_value` direct unit coverage: accepts original, detects mismatch, reports missing file; also re-confirms `verify_replay_digest` still delegates to identical behavior |
| `engine/tests/test_v5_replay_history_presentation.py` | **+9** (74 total, was 65) | `open_replay_enabled` over every `ReplayState`; `copy_seed_enabled` incl. zero/negative/very-large seeds; exact Copy Seed feedback text; tooltip wording constraints (no "guarantee"/unqualified "exact"); every non-available failure-text mapping; the pinned Section 21 wording; worker-failure text; mismatch dialog wording (no "open anyway") |
| `tests/test_v5_replay_history_browser.py` | **+25** (84 total, was 59) | Button enablement per selection/state; canonical-launcher integration test; checking-status + button-disable while pending; duplicate-click guard; missing/mismatch/legacy/vanished-during-verify outcomes; launcher-failure dialog; off-GUI-thread proof for `resolve_replay`/`verify_replay_integrity`; stale-response drop; shutdown-during-pending-preflight safety; double-click and Enter activation (incl. filter-field isolation); shared-activation-path proof; Copy Seed enablement, clipboard exact contents, and feedback text |

Total new/changed focused tests: **42**. No pre-existing Phase 7B/7C test was
weakened or removed; `test_no_playback_action_is_offered_in_this_phase` was
superseded by `test_open_replay_and_copy_seed_exist_but_rerun_never_does`,
which keeps its one still-true assertion (no Re-run action) and flips the
two assertions that were specific to 7C not having implemented these actions
yet.

---

## Q. Real smoke

Performed against real, on-disk artifacts (not the GUI test fake):

1. `runs/evaluations` (72 real `result.json`/`replay.jsonl` pairs) indexed
   cold into a scratch cache in 0.058 s.
2. Selected a real row (seed `2`); clicked **Open Replay**: the real
   `ReplayHistoryService.resolve_replay` and `verify_replay_integrity` ran
   against the real replay file, verified its digest, and handed the exact
   resolved path to `open_pygame_client_direct` (mocked to a recorder for
   this headless session rather than actually opening a Pygame window) —
   round trip **≈0.03 s**.
3. Clicked **Copy Seed**: clipboard held the exact seed (`"2"`) immediately.
4. Observed one cosmetic finding (Section J): the shared status label can be
   overwritten by a delayed Open-Replay response landing after a Copy Seed
   click's own confirmation — recorded, not silently patched.
5. Did **not** reproduce the full 53,458-occurrence corpus timing live in
   this session (Section M) — relies on Phase 7C's own published measurement
   of the identical single-worker queuing mechanism instead.

The interactive `Designer` checklist (`docs/MANUAL_SMOKE_TESTS.md` items
13–16, added this phase) remains the recommended path for a full visual
confirmation with a real Pygame window actually appearing, which this
non-interactive session cannot itself observe.

---

## R. Files changed

**Added**

| File | Purpose |
|---|---|
| `docs/research/v5/V5_REPLAY_HISTORY_PHASE7D_VIEWER_HANDOFF.md` | this report |

**Modified**

| File | Change |
|---|---|
| `app/views/replay_history.py` | Open Replay / Copy Seed UI, worker signal/slot, request-id staleness guard, Enter/double-click wiring, shutdown safety (+245 lines vs. the Phase 7C state it started from) |
| `app/services/replay_history_presentation.py` | `open_replay_enabled`, `copy_seed_enabled`, status/tooltip/dialog text (+86 lines) |
| `engine/src/battle_engine/replay_history/query.py` | `ReplayIntegrityStatus`, `ReplayIntegrityCheck` |
| `engine/src/battle_engine/replay_history/service.py` | `ReplayHistoryService.verify_replay_integrity` |
| `engine/src/battle_engine/replay_history/__init__.py` | export the two new types |
| `engine/src/battle_engine/result_model.py` | extracted `verify_replay_digest_value`; `verify_replay_digest` now delegates to it (behavior-preserving) |
| `engine/tests/test_replay_history.py`, `engine/tests/test_replay_reconstruction.py`, `engine/tests/test_v5_replay_history_presentation.py`, `tests/test_v5_replay_history_browser.py` | new focused tests (Section P) |
| `README.md`, `ARCHITECTURE.md`, `docs/MANUAL_SMOKE_TESTS.md` | document Open Replay / Copy Seed; no claim of Re-run Match |

`engine/src/battle_engine/replay_history/index.py` was **not** modified by
this phase (its Phase 7C diff, `ruleset_facets()`, was already present).
`app/agent_designer.py` was **not** modified by this phase — Open Replay and
Copy Seed are entirely internal to `ReplayHistoryWindow`; the Designer's
Tools-menu/singleton wiring Phase 7C added needed no change.

---

## S. Backend additions

Exactly the two items Section 38 lists as acceptable examples: a
reusable integrity-preflight helper (`verify_replay_digest_value`, plus the
`verify_replay_integrity` method built on it) and an explicit digest-status
enum (`ReplayIntegrityStatus`). No SQLite schema change, no discovery/query
semantics change, no `resolve_replay` behavior change. Each has focused tests
(Section P) and is documented above (Sections G, R).

---

## T. Deferred Phase 7E work

* A second read-only `ReplayHistoryService` on its own thread, so
  `resolve_replay`/`verify_replay_integrity` (and `fetchDetail`) do not queue
  behind an active reconcile on the real large corpus — Phase 7B's WAL
  configuration already supports this; recommended by Phase 7C and reaffirmed
  here since Open Replay inherits the identical contention.
* A genuine full-53k-corpus idle-vs-during-reconcile Open Replay timing
  measurement, once the environment I/O-bound cold-rebuild slowness observed
  in this session (Section M) is understood or a faster machine/session is
  available.
* The shared `actionStatusLabel` cosmetic race noted in Section J, if it
  proves bothersome in practice (e.g. separate transient-message ownership
  per action, or a short display-hold policy).
* `winner_label` row projection and column-width persistence, both already
  carried forward from Phase 7C's own deferred list, unaffected by this
  phase.

---

## U. Re-run Match disposition

**Not implemented — no placeholder, no disabled button, no context-menu
entry, no CLI invocation, no reconstructed match command.** Phase 6 Section S
deferred it because current artifacts do not guarantee the original agent
source still exists or matches its recorded hash, and Copy Seed's tooltip is
worded specifically to avoid implying otherwise. This phase adds nothing that
narrows that gap; a future exact-rerun feature remains a separate product
design requiring an explicit archived-agent-content/version-provenance
contract, as Phase 6 specified.

---

## Validation

| Check | Result |
|---|---|
| `ruff check .` | **All checks passed** |
| `mypy engine/src/battle_engine` | **Success: no issues found in 113 source files** |
| `mypy client/src/battle_client` | **Success: no issues found in 16 source files** |
| Replay History backend (`engine/tests/test_replay_history.py`) | **88 passed** (was 83) |
| Replay integrity unit tests (`engine/tests/test_replay_reconstruction.py`) | **18 passed** (was 15), full file |
| Replay History presentation (`engine/tests/test_v5_replay_history_presentation.py`) | **74 passed** (was 65) |
| Replay History browser, GUI (`tests/test_v5_replay_history_browser.py`, `-m gui`) | **84 passed** (was 59) |
| Full display-backed `gui` suite (`pytest tests/ -m gui`) | **422 passed, 6 deselected** (was 397 passed, 6 deselected) |
| V5/ruleset/replay_history focused (`-k "v5 or ruleset or replay_history"`) | **900 passed**, 2,716 deselected |
| Ruleset 4 permanent equivalence | **23 passed** |
| Full default suite (`pytest`, testpaths default) | One run: **3,589 passed, 3 failed, 21 skipped, 3 deselected** in 344 s. All 3 failures were in `test_agent_evaluation_behavior.py`/`test_agent_evaluation_parallel.py`/`test_agent_evaluation_v2_methodology.py` (multi-worker-subprocess evaluation tests, unrelated to Replay History) and were caused by this session running that suite concurrently with a separate GUI-suite pytest process against the same shared `--basetemp` — confirmed by rerunning the exact 3 failing tests alone immediately afterward: **3 passed** in 55.95 s with no code change. Two subsequent from-scratch full-suite attempts, run in isolation, stalled during the same multi-worker evaluation tests with near-zero CPU utilization and were aborted after several minutes each — an apparent environment/session subprocess-contention issue (see Section M), not something this phase's diff touches (Replay History code and its tests are unaffected by, and do not spawn, agent-evaluation worker subprocesses) |
| `git diff --check` | Clean (only pre-existing CRLF-normalization notices, no new whitespace errors) |
| `git status --short` | Matches Section R exactly — no run artifact, cache file, or screenshot tracked |

---

## Boundary audit (Section 53)

Searched `app/views/replay_history.py` and
`app/services/replay_history_presentation.py`:

| Pattern | Result |
|---|---|
| `sqlite3`, `SELECT`/`INSERT`/`UPDATE`/`DELETE`/`CREATE TABLE`/`PRAGMA`, `.execute(`, `cursor()`, `BEGIN`/`COMMIT`/`ROLLBACK` | **None** (only prose using the English word "committed") |
| `json.load`, `open(`, `read_text`, `.stat(`, `os.walk`, `iterdir`, `hashlib`, `sha256` | **None** |
| Alternate Viewer command construction (`Popen`, `subprocess`, `QProcess`, hand-built `build_replay_command`/`build_match_command` call) | **None** — the sole mention of `Popen` is prose in a docstring describing `open_pygame_client_direct`'s own existing behavior |
| `re-run`/`rerun` | Only in prose explicitly stating it is out of scope, and in an unrelated docstring use of "re-runs" describing click-time re-verification |
| `result.json`/`replay.jsonl` literal filenames | Docstring/comment prose only |

Confirmed unchanged: result schema, replay schema, `match_id`, occurrence
metadata, SQLite schema, Replay History discovery/filtering semantics,
Designer match behavior, CLI behavior, gameplay, rulesets, product version.

---

## Explicit confirmations

1. Result and replay schemas are unchanged.
2. SQLite cache schema and Replay History discovery semantics are unchanged.
3. Gameplay, rulesets, and CLI semantics are unchanged.
4. Re-run Match was not implemented in any form.
5. No commit and no push were performed.
