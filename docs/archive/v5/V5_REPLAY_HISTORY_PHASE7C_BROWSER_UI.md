# Bytefray V5 — Phase 7C: Replay History Browser UI

Phase 7C brings the Qt-free Phase 7B service into the Agent Designer as
**Tools → Replay History…**: a modeless, virtualized browser over every
completed match Bytefray has written, paged and filtered entirely by the
backend, on a dedicated worker thread.

Phase 7B is consumed, not re-implemented. The UI issues no SQL, opens no
artifact, and decides no history semantics. Replay availability is reported as
a state; nothing opens a replay, copies a seed, or re-runs a match — those
remain Phase 7D.

---

## A. Starting state

| Fact | Value |
|---|---|
| Branch | `v5-research` |
| HEAD at start | `c265fddc5e703108c5de199977eedda8b6ffd02a` |
| Upstream | `origin/v5-research`, 0 ahead / 0 behind |
| Working tree | Clean — no modified, staged, or untracked files |
| Bytefray version | `5.0.0a1` (unchanged) |
| Phase 7B present | Yes — `battle_engine/replay_history/` committed at `c265fdd` |

No unrelated file was touched; the final `git status` contains only this
phase's work (Section W).

---

## B. UI architecture

Three modules, split along the Qt boundary the repository already enforces
(`app/services/*` is Qt-free; `app/views/*` is Qt):

| Module | Lines | Role |
|---|---:|---|
| `app/services/replay_history_presentation.py` | 1,103 | **Qt-free.** Column set and formatting, the `≈` approximate-time marker, stable-identifier→label maps, detail-pane grouping, filter-state→`HistoryQuery` mapping, status/empty-state copy. |
| `app/views/replay_history.py` | 1,304 | **Qt.** `ReplayHistoryWorker`, `ReplayHistoryTableModel`, `ReplayHistoryDetailPane`, `ReplayHistoryWindow`. |
| `app/agent_designer.py` | +46 | Tools action, singleton window, shutdown join. |

Putting every *decision* in the Qt-free module is what makes the presentation
contract testable headlessly (65 tests in the default suite) rather than only
behind a display.

### Window

`ReplayHistoryWindow(QDialog)`, shown with `show()` — **modeless**. The
existing `EvaluationHistoryDialog` is modal (`exec()`), but modality is
incompatible with two explicit Phase 7C requirements: browsing history
alongside the Designer, and raising an already-open browser instead of opening
a second one. `QDialog` is still the repository's dialog idiom, so Escape-closes
and the `QDialogButtonBox(Close)` footer behave as they do elsewhere.

### Table model

`ReplayHistoryTableModel(QAbstractTableModel)` holds `HistoryRow` DTOs — never
a database row, a cursor, or a widget per occurrence — and implements Qt's own
`canFetchMore`/`fetchMore` protocol, served asynchronously (Section N).

### Detail pane

`ReplayHistoryDetailPane(QScrollArea)` renders `DetailSection`/`DetailField`
values as `QGroupBox` + `QFormLayout`, which gives each field an accessible
name for free. Sections marked `advanced=True` appear only under
**Show technical details**.

---

## C. Thread ownership

> **The GUI thread never constructs, uses, or closes the Replay History
> `ReplayHistoryService`.**

| Owner | Owns |
|---|---|
| GUI thread | Widgets, `QAbstractTableModel` state, filter state, generation counters |
| Worker thread (`QThread`, `bytefray-replay-history`) | `ReplayHistoryService` and its SQLite connection — created, used, and closed here |

The service is constructed in the worker's `start()` slot, **not** in
`ReplayHistoryWorker.__init__`: the worker object is built on the GUI thread
and then moved, and a SQLite connection belongs to the thread that will use it.

Everything crossing back is a frozen DTO — `OpenResult`, `PageResult`,
`DetailResult`, `RefreshResult`, `WorkerError`, plus Phase 7B's own
`HistoryRow`/`HistoryDetail`/`RulesetFacet`. No service, connection, cursor, or
live model object crosses.

Requests travel the other way as **signals** (`pageRequested`,
`detailRequested`, `refreshRequested`, `facetsRequested`, `shutdownRequested`)
connected to worker slots, which Qt delivers as queued invocations carrying the
Python objects untouched.

The single deliberate exception is cancellation. `requestCancel()` sets a
`threading.Event` **directly from the GUI thread**, because a queued cancel
signal would sit in the worker's event queue *behind* the very refresh it is
meant to interrupt. A shared flag is the only mechanism that reaches a running
call, and it is exactly the shape `cancel_check` expects.

This is asserted mechanically, not by inspection: the test fake records
`threading.get_ident()` for every call it receives, and
`test_every_service_call_happens_off_the_gui_thread` proves `open`,
`fetch_page`, `count`, `fetch_detail`, `ruleset_facets`, `refresh` and `close`
all land on one non-GUI thread.

---

## D. Worker lifecycle

```
AgentDesigner
  └─ ReplayHistoryWindow (modeless QDialog, singleton)
       └─ QThread "bytefray-replay-history"
            └─ ReplayHistoryWorker
                 └─ ReplayHistoryService  (SQLite)
```

**Startup.** `QThread.start()` → `started` → `worker.start()` opens the service
and emits `opened` with the cache state.

**Shutdown** (`closeEvent`, or `shutdownWorker()` called by the Designer):

1. set the cancel flag (reaches a running scan immediately);
2. emit `shutdownRequested` (queued);
3. the worker's `shutdown()` closes the service on the thread that opened it,
   then calls `QThread.currentThread().quit()`;
4. the GUI thread `wait()`s up to 15 s.

Quitting from *inside* the worker is deliberate: the GUI thread is blocked in
`wait()`, so a queued `quit()` back to the GUI thread would deadlock against
exactly that wait. `wait()` on the GUI thread does not stop the worker's own
event loop, so the queued shutdown still arrives.

`QThread.terminate()` is never called. If the 15 s wait ever elapsed, the
window reports that a background scan is still finishing and leaves the thread
alone rather than abandoning an open SQLite connection mid-transaction.

No `QThread: Destroyed while thread is still running` warning was produced on
any tested close path (Section T) or during the real Designer smoke.

---

## E. Designer integration

`Tools → Replay History…`, added immediately after the existing
`Evaluation History…`. Nothing else in the Tools menu moved.

* Enabled unconditionally — it neither requires a selected agent nor conflicts
  with a running match, because browsing executes no agent code and spawns no
  process.
* Opening does no corpus work on the GUI thread: the window appears, its worker
  opens the index, and reconciliation follows in the background.
* **Singleton.** `AgentDesigner._replay_history` holds the one instance;
  re-activating the action calls `show()`/`raise_()`/`activateWindow()` rather
  than starting a second background scan over the same run tree.
* The window carries `WA_DeleteOnClose` and emits its own `windowClosed`
  signal, which the Designer uses to drop the reference. Relying on Qt's
  `destroyed` alone would leave a window closed but still referenced for one
  event-loop pass, so a reopen in that window would raise an already-shut-down
  browser with a permanently disabled Refresh (regression-tested).
* `AgentDesigner.closeEvent` calls `shutdownWorker()` before its children are
  destroyed.

---

## F. Startup flow (cached first)

1. worker opens the service and reports the cache state;
2. **first page requested immediately** — before any filesystem work;
3. rows render as soon as they arrive;
4. ruleset facets requested;
5. reconciliation starts in the background;
6. on completion the current query is re-issued and the summary is reported.

Measured on the real 53,458-occurrence corpus: rows on screen **18–31 ms**
after the action fires, while reconciliation continues for a further ~8.5 s.
`test_cached_rows_appear_before_reconciliation_finishes` pins the ordering by
holding the refresh open and asserting rows arrive while it is still running.

---

## G. First-use flow (no cache)

The window shows immediately with a **"Preparing Replay History…"** state
(never a frozen window and never an error), the worker builds the index, and
rows populate when the first query succeeds. The Designer stays fully usable
throughout; a full build over this corpus is minutes of worker-thread work and
costs the GUI thread nothing.

---

## H. Main layout

```
┌ Filters ───────────────────────────────────────────────────────────────┐
│ Search entrants: [____]  Ruleset: [▾]  Result: [▾]                     │
│ Source: [▾]              Replay:  [▾]  Seed:   [____]                  │
│ ☐ From: [date]  ☐ To: [date]                        [ Clear Filters ]  │
└────────────────────────────────────────────────────────────────────────┘
 status / progress text                       [progress] [Cancel] [Refresh]
┌──────────────── history table ─────────────┐┌──── detail pane ─────────┐
│ Date │ Entrants │ Result │ Ruleset │ Seed …││ (non-durable notice)     │
│                                            ││ Match / Entrants /       │
│  (or empty-state page)                     ││ Result / Replay          │
│                                            ││ ☐ Show technical details │
└────────────────────────────────────────────┘└──────────────────────────┘
                                                                  [ Close ]
```

Default 1360×780, resizable, `QSplitter` at 940/400. Bytefray has no
table-state or geometry persistence mechanism, and Phase 7C explicitly declined
to introduce one for a single tool window, so nothing is persisted.

Table and empty states share a `QStackedWidget`, so an empty result replaces
the table rather than leaving a blank grid.

---

## I. Table columns

Exactly the Phase 6 Section O MVP set — no debug columns:

| Column | Width | Formatting |
|---|---:|---|
| Date | 165 | Localized; `≈` prefix when inferred; `Unknown` when absent; health marker prepended |
| Entrants | stretch | `A vs B`; beyond three, `First and N others` (full list in tooltip and details) |
| Result | 120 | Winner value, `Tie`, `Unknown`, `Invalid metadata`, `No result recorded` |
| Ruleset | 130 | `Ruleset v4 alpha1`; exact ID in tooltip and details |
| Seed | 105 | Integer, right-aligned; `—` when absent |
| Source | 95 | `Designer`, `Agent Test`, `Tournament`, `Evaluation`, `CLI Latest`, `Other Run`, `Unknown` |
| Replay | 100 | The 7B enum vocabulary verbatim |

Widths were measured against real rendered content in the shipped UI font
(Segoe UI), not guessed. Entrants is the one column with unbounded content, so
it takes the leftover width; the initial splitter sizes exist because stretch
factors alone left the table too narrow for it to receive *any* leftover,
collapsing it to the smallest column on screen — found by looking at the
rendered window (Section S).

Ruleset labels are derived from the identifier's own shape rather than a fixed
table, so a historical or research Ruleset the product no longer offers still
reads correctly; anything unrecognized falls back to the exact ID.

---

## J. Timestamp presentation

| Confidence | Display | Detail "Time source" |
|---|---|---|
| `recorded` | `Sep 11, 2026 3:42 PM` | Recorded by the match |
| `directory_inferred` | `≈ Sep 11, 2026 3:42 PM` | Approximate — inferred from the run folder name |
| `filesystem_fallback` | `≈ Sep 11, 2026 3:42 PM` | Approximate — file modification time |
| unknown | `Unknown` | Unavailable |

The marker is **text**, not styling, so the distinction survives a screen
reader, a copied cell, and a monochrome display. Tooltip: *"Approximate time
inferred from historical artifact metadata."*

Display always derives from `effective_timestamp_ns`, never the stored string:
a recorded `completed_at` keeps whatever offset the writer used while a
fallback is normalized UTC, and the epoch field is the one uniform
representation. Unknown never renders as a 1970 epoch date.

The entire real corpus is `filesystem_fallback`/`directory_inferred`, so every
row in the smoke screenshots carries `≈` — the fallback path is what this
corpus actually exercises.

---

## K. Health and replay-state presentation

Health is never carried by color. Every unhealthy row gets:

* a **text marker** in the Date cell — `!` degraded, `?` replay-only, `×` invalid;
* the explanation appended to **every** column's tooltip;
* a `Status` field in the detail pane;
* inclusion in the row's `AccessibleTextRole` summary.

| `EntryHealth` | Label | Marker |
|---|---|---|
| `healthy` | Complete | — |
| `degraded` | Replay unavailable | `!` |
| `incomplete` | Replay only | `?` |
| `invalid` | Unreadable result | `×` |

All six `ReplayState` values have a label and a plain-language tooltip.
Degraded rows stay fully browsable and selectable — one malformed artifact
never turns the browser into an error state, which is asserted directly
(`test_degraded_row_carries_a_text_marker_and_stays_browsable`).

---

## L. `_loose` / non-durable presentation

`runs/_loose` is `cli_latest` with `durable_location = False`. It is shown, not
hidden, and marked:

* row tooltip carries the notice;
* the accessible row summary says "not durable history";
* selecting it shows a prominent notice directly above the detail pane:
  > CLI Latest is overwritten by the next loose CLI run. This entry is not durable history.

Phrased as information, never an error — asserted by
`test_loose_notice_is_informational_not_phrased_as_an_error`, which fails if
the wording acquires "error", "corrupt", or "failed".

`non_durable_note(detail)` is the single source for this decision, so the
sentence is decided once and rendered once. (It was initially rendered twice —
as a pane header *and* a Match-section note — visible in the first screenshot
pass and removed.)

---

## M. Filters and backend mapping

All seven Phase 6 MVP filters. No presets, no tags/notes.

| Control | `HistoryQuery` field |
|---|---|
| Entrant search (debounced) | `entrant_text` (empty → `None`) |
| Ruleset | `ruleset_ids=(id,)`, or `(None,)` for "No Ruleset recorded" |
| Result | `outcome_states` — All / Has a winner / Tie / Unknown |
| Date from/to | `start` / `end`, aware local datetimes at day bounds |
| Seed | `seed` (exact integer) |
| Source | `workflows=(WorkflowSource(value),)` |
| Replay | `replay_states=(ReplayState(value),)` |
| Clear Filters | resets every control to the unfiltered state |

`HistoryFilterState` is a frozen dataclass with `to_query()`; the widgets hold
no query logic, and every offered combo value is proven mappable.

**Seed input** is tolerant: an unparseable partial entry marks the field
inline (tooltip + accessible description) and constrains *nothing*, because the
user is mid-typing and an empty table would be a misleading answer to an
unfinished question. No dialog is ever raised on a keystroke.

**Clear Filters** touches only filter controls — the technical-details toggle
and splitter position are explicitly asserted to survive it.

**Result filter — a deliberate narrowing.** Phase 7C suggested "specific winner
search/selection as supported by backend API". The backend's `winner` filter is
*exact-match* and there is no winner-discovery facet, so such a control would
demand a string the user cannot see. Entrant search already answers "matches
involving X". Recorded here rather than silently dropped.

---

## N. Paging

500-row keyset pages via the backend cursor. No `OFFSET` is constructed
anywhere, and `HistoryCursor` values are only ever passed back as received.

The model implements Qt's `canFetchMore`/`fetchMore`, so the view asks for more
as it approaches the end; `fetchMore` starts an asynchronous request and the
rows are inserted with `beginInsertRows` when the worker answers. A
`_fetch_pending` guard prevents duplicate in-flight requests.

`suspendFetching()` is called whenever a new first page is requested. Between
that moment and the reply the model still holds the *previous* query's rows, so
leaving `canFetchMore` true invited a continuation with no valid cursor — a
request that was silently dropped, leaving a view scrolled to the bottom stuck
until the user scrolled again. Found by tracing page requests against
responses, not by reading the code.

Measured: page 2 in 6 ms, pages 3–5 in 21–26 ms, on the 53k corpus.

---

## O. Detail pane

| Section | Fields | Visibility |
|---|---|---|
| **Match** | Time, Time source, Status, Source, Ruleset, Ruleset provenance, Seed, Mode, arena/tick/win-mode configuration | always |
| **Entrants** | Ordered name, agent ID, runtime kind, Agent API version, agent version; resolved Agent Params; content hash in tooltip | always |
| **Result** | Outcome, Winner (omitted for a tie), Score, Termination, Ticks | always |
| **Replay** | Replay state, bounded diagnostic note | always |
| **Identity** | Occurrence, Identity source, Match ID, Result ID | technical details |
| **Artifact** | Result file/state/schema, product version, sizes, replay file/schema, first indexed, duplicate flag, other configuration | technical details |

**Legacy identity.** A v1 artifact's synthetic key is never presented as a
persisted UUID: it reads `legacy-location_… (synthetic legacy identifier)` with
an Identity source of *"Synthetic legacy identifier — this artifact predates
recorded occurrence identity and has no persisted UUID."* A v2 occurrence shows
its authoritative UUID normally.

**Winner naming.** `result.json` records the winner as an `agent_id` (`"A"`),
which tells a reader nothing beside a row of real agent names. The
ordinal→name mapping exists on the detail's entrants, so the detail pane
resolves it to `Viper (B)`; an unmatched value is shown verbatim rather than
replaced by a guess. The compact row projection carries no such mapping — see
Section X.

**Ties** no longer render a `Winner` row: `result.json` records `winner: "tie"`,
which read as a competitor's name.

**Diagnostics** are the backend's bounded strings only. A malformed artifact
produces a short explanation; a test asserts no traceback, no SQL, no artifact
body, and a total rendering under 4,000 characters.

Every field tolerates `None` — a legacy artifact legitimately has no occurrence
UUID, product version, or recorded time.

---

## P. Progress and cancellation

Backend progress arrives every 1,000 candidates and is coalesced to at most one
status update per 120 ms. Text is user-facing — *"Checking for new matches —
1,000 artifacts scanned…"* — and never mentions SQLite. The progress bar is
indeterminate because the backend reports artifacts seen, not a total.

During a refresh: progress bar and **Cancel** visible, **Refresh** disabled.
Otherwise the reverse.

Cancellation is cooperative via 7B's `cancel_check` (polled every 256
artifacts). After a cancel the backend has rolled back, so the displayed rows
still exactly match the committed index and are left untouched — no re-query.
The status reads **"Refresh cancelled."** and is asserted to contain neither
"error" nor "failed".

Measured acknowledgement: **10–35 ms** on the real corpus.

**One real bug fixed here.** `refresh()` originally cleared the cancel flag on
entry. A cancel (or a shutdown) raised while the refresh slot was still queued
behind an earlier request was therefore discarded, and the whole corpus scan
ran anyway — visible as a close that hung for the length of a scan. The
requester now owns the flag's lifetime and the operation only reads it.

---

## Q. Empty, error and cache-recovery states

| State | Copy |
|---|---|
| No history | "No match history yet" / "Completed Bytefray matches will appear here. A match is listed once it has written a result file under the Bytefray runs folder." |
| Filters match nothing | "No history matches the current filters" / "Adjust or clear the filters to see more matches." + **Clear Filters** |
| Preparing | "Preparing Replay History…" |
| Open failure | "Replay History is unavailable" + the concise reason; Refresh disabled |

Worker exceptions are captured per operation and converted to `WorkerError`
signals — none can escape into the Qt event loop. A query, refresh, or facet
failure **keeps the existing rows visible**: a transient read problem must not
throw away a usable list.

**Cache recovery wording is deliberate.** A missing or corrupt cache produces
"Preparing Replay History for the first time…" or "Rebuilding Replay History
index…" — never a claim that the user's history is damaged, because only the
disposable index is. A test fails if that copy ever acquires "corrupt" or
"lost". A non-persistent cache is reported as session-only.

---

## R. Accessibility and keyboard support

* Every filter control has a `setBuddy` label with a mnemonic
  (`&Search entrants`, `&Ruleset`, `Res&ult`, `S&ource`, `Re&play`, `See&d`,
  `Fro&m`, `&To`, `&Clear Filters`, `&Refresh`) and an `accessibleName`.
* Table, status label and progress bar carry accessible names; every detail
  field label becomes its value widget's accessible name, tooltips become
  accessible descriptions.
* `AccessibleTextRole` on a row yields one spoken summary including health in
  words and non-durability where it applies.
* Row selection, `SelectRows` behavior, and arrow-key navigation work; Escape
  closes the dialog per normal app behavior.
* **No Enter/double-click playback semantics are assigned**, because 7D has not
  implemented playback. Binding them now would create an action that silently
  does nothing.
* Health and approximation are text, never color alone.

---

## S. Performance (real corpus)

Real `runs/` tree, Windows 11 `10.0.26120`, Python 3.13, **53,458
occurrences**, cache 99.8 MB.

### Backend, this machine

| Operation | Measured |
|---|---:|
| Service open | 8.5 ms |
| Cached first page (500) | 7.0 ms |
| `count()` unfiltered | 0.5 ms |
| Second keyset page | 5.0 ms |
| Detail fetch | 1.4 ms |
| `ruleset_facets()` (new) | 63–76 ms |
| Warm reconcile, 53,458 unchanged | **8.5 s** |

Consistent with Phase 7B's figures (it measured 7.4 s warm reconcile). A *full
cold rebuild* on this machine measured 279 s against 7B's 26 s — the difference
is cold filesystem cache and on-access scanning, not a regression; the warm
reconcile above is the path that actually runs in the product.

### UI-side

| Measurement | Result |
|---|---:|
| Construct + show window | 10–21 ms |
| **Open → first rows visible** | **18–31 ms** |
| Next 500 rows (pages 3–5) | 6–26 ms |
| Filter round trip (ruleset / replay / clear) | 21–41 ms |
| Entrant filter incl. 300 ms debounce | 355–373 ms (≈70 ms of query) |
| Detail after selection (worker idle) | 7 ms |
| Cancel acknowledged | 10–35 ms |
| Close (joins worker) | 8–12 ms |
| **Worst GUI-thread block during the 8.5 s reconcile** | **27 ms** |
| 6 rapid keystrokes → backend queries | **1** |

Measured with a 16 ms heartbeat timer recording how late it actually fires, so
"worst GUI block" is the longest uninterrupted stall the event loop suffered.
The UI target — *no perceptible multi-second GUI freeze* — is met with a wide
margin, and the backend's 5 ms first-page advantage is preserved end to end.

### The one honest cost: query serialization behind a refresh

Phase 7C specifies **one** worker. Detail and page queries therefore queue
behind a running reconcile on that thread. Measured in the real Designer smoke:
selecting a row while the startup reconcile was running took **7.4 s** to
populate details — the reconcile's own duration, not a GUI stall.

This is disclosed rather than hidden: the pane reads *"Loading match details
(waiting for the history refresh to finish)…"* while it waits. The GUI thread
is never blocked, filters remain typeable, the table stays scrollable, and the
already-loaded rows stay usable.

Phase 7B's WAL configuration was explicitly designed so "readers stay on the
last committed generation while one refresh writer commits a new one", so a
second read-only service on its own thread would remove this window. That is an
architecture change beyond 7C's stated scope and is recommended for 7E
(Section Y) rather than smuggled in here.

---

## T. Tests

| Module | Tests | Marker |
|---|---:|---|
| `engine/tests/test_v5_replay_history_presentation.py` | **65** | headless — runs in the default suite |
| `tests/test_v5_replay_history_browser.py` | **59** | `gui` — display-backed workflow |

Split follows the repository convention: Qt-free Designer logic is tested under
`engine/tests` (as `test_v5_alpha1_phase_e_designer_services.py` already does),
Qt widgets under root `tests/` with a `gui` marker.

**Headless (65)** — columns; recorded vs directory-inferred vs filesystem
fallback vs unknown timestamps; entrant pair and many-entrant collapse; every
outcome and degraded/invalid result text; six historical ruleset labels
including `bytefray-rules-3-alpha1` and `bytefray-rules-5-r1-alpha1`;
`N/A` vs `Unknown`; seed; workflow and replay-state label coverage for every
enum member; health markers and tooltips; `_loose` marking and tone; v1 vs v2
identity display; detail grouping, winner naming, tie suppression, `None`
tolerance, diagnostic bounding; every filter's query mapping; seed parsing and
large seeds; date bounds; ruleset facets against a real index. Rows and details
come from the **real Phase 7B service** wherever the fact under test is a
backend fact, so a backend normalization change fails here rather than drifting
past a hand-built fixture.

**GUI (59)** — thread ownership (4), lifecycle (9), cached-first and first-run
(3), table model (9), paging (4), filters (9), details (6), refresh/progress/
cancellation (7), accessibility/keyboard (3), Designer integration (6).

Four of these were written as regressions for defects found during this phase,
and each was confirmed to fail against the pre-fix code:

| Defect | Test |
|---|---|
| Refresh summary overwritten by the follow-up row count | `test_refresh_summary_survives_the_requery_that_follows_it` |
| Cancel discarded when raised while refresh was still queued | `test_a_cancel_raised_while_refresh_is_still_queued_is_not_lost` |
| Detail pane painted stale section widgets underneath new ones | `test_reselecting_rows_does_not_accumulate_stale_detail_widgets` |
| Singleton slot freed only on Qt's deferred deletion | `test_closing_the_browser_immediately_frees_the_designer_slot` |

The GUI suite was run **nine consecutive times** while chasing an intermittent
failure; the two races it exposed are fixed and all runs since are clean.

---

## U. Backend boundary audit

Searches over `app/views/replay_history.py` and
`app/services/replay_history_presentation.py`:

| Pattern | Result |
|---|---|
| `sqlite3`, `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE TABLE/INDEX`, `PRAGMA`, `.execute(`, `cursor()`, `BEGIN`, `COMMIT`, `ROLLBACK` | **None** |
| `json.`, `open(`, `read_text`, `.stat(`, `os.walk`, `iterdir`, `hashlib`, `sha256` | **None** |
| `result.json` / `replay.jsonl` | Docstring prose only |
| `open_pygame_client_direct`, `build_replay_command`, `resolve_replay`, clipboard, re-run | **None** (a docstring naming them as deferred) |

The only backend entry point the client touches is
`ReplayHistoryService.open(...)` and the typed methods on the returned service.
The UI derives no timestamp fallback, computes no identity, and determines no
health state; it formats already-normalized values and nothing else.

---

## V. Documentation changes

| File | Change |
|---|---|
| `README.md` | One bullet in the Agent Designer feature list describing **Tools → Replay History…**, stating explicitly that opening a replay from History is not yet implemented. |
| `ARCHITECTURE.md` | A short entry describing the module boundary and the worker-thread ownership model — the first mention of `battle_engine.replay_history` in this document. |
| `docs/MANUAL_SMOKE_TESTS.md` | A 12-step "Replay History browser" interactive checklist alongside the existing Designer sections. |

No documentation claims Viewer launch, Copy Seed, or Re-run Match exists.

---

## W. Files changed

**Added**

| File | Lines |
|---|---:|
| `app/views/replay_history.py` | 1,304 |
| `app/services/replay_history_presentation.py` | 1,103 |
| `engine/tests/test_v5_replay_history_presentation.py` | 820 |
| `tests/test_v5_replay_history_browser.py` | 1,224 |
| `docs/research/v5/V5_REPLAY_HISTORY_PHASE7C_BROWSER_UI.md` | this report |

**Modified**

| File | +/− | Change |
|---|---|---|
| `app/agent_designer.py` | +46/−1 | Tools action, singleton window, shutdown join |
| `engine/src/battle_engine/replay_history/query.py` | +24 | `RulesetFacet` |
| `engine/src/battle_engine/replay_history/index.py` | +23 | `HistoryIndex.ruleset_facets()` |
| `engine/src/battle_engine/replay_history/service.py` | +11 | service passthrough |
| `engine/src/battle_engine/replay_history/__init__.py` | +2 | export |
| `ARCHITECTURE.md` | +16 | module boundary |
| `docs/MANUAL_SMOKE_TESTS.md` | +51 | smoke checklist |
| `README.md` | +5 | Designer feature bullet |

No deletions. No SQLite cache, database, or screenshot artifact is tracked.

---

## X. Deviations from Phase 6 / 7B

### 1. One backend addition — `ruleset_facets()` (proven, not assumed)

Phase 7C requires historical Rulesets to remain filterable and discourages
hardcoding an incomplete list. Phase 7B exposed no distinct-value API.

Before adding anything, the real corpus was measured:

| Ruleset | Rows | In `DESIGNER_RULESET_OPTIONS`? |
|---|---:|---|
| `bytefray-rules-2` | 31,053 | yes |
| `bytefray-rules-4-alpha1` | 12,782 | yes |
| **`bytefray-rules-3-alpha1`** | **6,984** | **no** |
| `bytefray-rules-4` | 1,910 | yes |
| `bytefray-rules-1` | 673 | yes |
| **`bytefray-rules-5-r1-alpha1`** | **42** | **no** |
| `bytefray-rules-4-alpha2` | 7 | yes |
| **`bytefray-rules-5-r2-alpha1`** | **7** | **no** |

The product's own option list omits **7,033 real rows**. Reusing it would make
those matches unfilterable; discovering them in the UI would mean paging the
whole corpus — exactly the backend work 7C must not do.

The addition is minimal and additive: one `GROUP BY` over two already-indexed
columns, one frozen `RulesetFacet` DTO, one service passthrough. **No schema
change, no column added, no cache version bump, no existing behavior altered.**
Measured 63–76 ms on 53,458 rows, called once per open and once per refresh, on
the worker thread. It is visible in the real product — the Ruleset filter lists
all eight identities with counts.

### 2. Modeless window rather than the existing modal dialog convention

`EvaluationHistoryDialog` uses `exec()`. Modality is incompatible with Phase
7C's "prefer modeless" and "raise the existing window" requirements. `QDialog`
is retained so Escape and the Close button behave conventionally.

### 3. Result/winner filter narrowed to outcome classes

See Section M — the backend's exact-match `winner` filter has no discovery
facet, so a winner control would demand an invisible string.

### 4. Row-level winner shows the recorded value, not a display name

Phase 6 Section O specifies "winner display name" in the Result column. The
compact `HistoryRow` projection carries `winner` (an `agent_id`) but no
ordinal→name mapping, so the row shows `A`/`B` where the result recorded that.
The **detail pane does resolve it** (Section O), since `HistoryDetail` carries
the entrants.

Closing this at row level would require a stored `winner_label` column — a 7B
cache schema change, which Phase 7C prohibits absent a proven blocker. This is
a display shortfall, not a correctness one, and is recommended for 7D/7E.

---

## Y. Deferred Phase 7D work

* Open Replay / Viewer handoff (`open_pygame_client_direct`,
  `build_replay_command`), including double-click and Enter semantics
* Replay digest preflight against `ReplayResolution.expected_sha256`
* Copy Seed
* Re-run Match

Recommended for 7E consideration:

* A second read-only service on its own thread so queries do not serialize
  behind a refresh (Section S) — WAL already supports it
* A `winner_label` row projection (Section X.4), if a cache schema bump is ever
  otherwise warranted
* Column-width / geometry persistence, if Bytefray gains a general table-state
  mechanism

---

## Z. Phase 7D contract

7D can add its actions without rearranging this window.

**Selected occurrence.** `ReplayHistoryWindow._selected_location` holds the
current `location_id` (`None` when nothing is selected), maintained by
`_onRowChanged`/`_clearSelection` and preserved across a refresh where the row
survives. `self.model.rowAt(index.row())` yields the full `HistoryRow`; the
last fetched `HistoryDetail` backs the detail pane.

**Adding a worker call** is three symmetrical pieces, matching every existing
one:

```python
# window
replayRequested = Signal(str, int)                 # location_id, generation
self.replayRequested.connect(self._worker.resolveReplay)   # in _connectWorker

# worker
@Slot(str, int)
def resolveReplay(self, location_id: str, generation: int) -> None:
    resolution = self._service.resolve_replay(location_id)   # 7B, ~0.5 ms
    self.replayResolved.emit(ReplayResolutionResult(generation, resolution))
```

`resolve_replay` re-resolves and re-checks the path every time and must be
called at click time, never cached across a user action.

**Where the controls go.** `_buildDetailArea()` already has a vertical layout
above `advancedCheck`; an action row there needs no layout change elsewhere. No
placeholder buttons exist to remove — 7C deliberately ships none, and a test
(`test_no_playback_action_is_offered_in_this_phase`) fails if an "Open Replay",
"Copy Seed", or "Re-run" button appears before it works.

**Keyboard.** Enter and double-click on the table are intentionally unbound and
free for 7D to claim.

---

## Validation

| Check | Result |
|---|---|
| `ruff check .` | **All checks passed** |
| `mypy engine/src/battle_engine` | **Success: no issues found in 113 source files** |
| `mypy client/src/battle_client` | **Success: no issues found in 16 source files** |
| V5 / ruleset focused (`-k "v5 or ruleset or replay_history"`) | **884 passed**, 2,211 deselected |
| Ruleset 4 permanent equivalence | **23 passed** |
| Phase 7B backend suite | **83 passed** |
| Full automated suite | **3,575 passed, 21 skipped, 3 deselected** (5:52) |
| Baseline full suite (new module ignored) | 3,510 passed, 21 skipped, 3 deselected |
| Test-count delta | +65, exactly the new headless module — no pre-existing test changed |
| Display-backed `gui` suite | **397 passed**, 6 deselected (338 pre-existing + 59 new) |
| Real Designer GUI smoke | **Passed** — see Section S |
| `git diff --check` | Clean |
| Gameplay / ruleset / CLI changes | **None** |
| Result / replay schema changes | **None** |
| Commit / push | **None performed** |
