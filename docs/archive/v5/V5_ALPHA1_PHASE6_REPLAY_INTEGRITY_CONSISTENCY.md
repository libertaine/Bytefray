# V5 Alpha 1 Phase 6 — Replay Integrity Consistency

Scope: audit every user-facing replay-opening path and make recorded-result
replay actions verify the canonical result/replay relationship at click time.
This phase does not change replay or result schemas, persistence, gameplay,
history indexing, or standalone replay-file support.

## 1. Baseline and process safety

The phase began on 2026-09-13 with:

| Item | Initial state |
|---|---|
| Branch | `v5-research`, tracking `origin/v5-research` |
| HEAD | `7daa7beeb3bfde533fd62e3308a42e047ec219e6` (`refactor(v5): organize application history navigation`) |
| Phase 5 | Committed at HEAD |
| Working tree | Clean (`git status --short --branch` reported only the branch/tracking line) |
| Git lock | No `.git/index.lock` |
| Process audit | No Python, pytest, Claude, Gemini, Antigravity, replay-viewer, or other checkout worker was active. The only broad-name match was the expected current Codex application process. |

No reset, restore, clean, stash, commit, or overlapping pytest run was
performed.

## 2. Complete replay-opening inventory and before-state matrix

This matrix was completed before implementation. “Load” means the result or
history window's initial/adaptation check; “click” means a check immediately in
the user action that hands the path to Replay Viewer.

| User-visible path | Source and replay-path derivation | Result identity / replay association | SHA-256 | Load vs click | Missing / changed / replaced behavior before Phase 6 | User error and launcher |
|---|---|---|---|---|---|---|
| Simple **View Last Match** | Session `_last_replay`, originally derived from the just-written `result.json` | No click-time result read or identity/association check | No | Existence at click only | Missing showed a warning and then offered the arbitrary-file picker; changed or replaced content launched | `Replay Not Found`, then `open_pygame_client_direct` |
| Advanced **View Last Match** | Same shared `_last_replay` and handler as Simple | Same as Simple | No | Existence at click only | Same as Simple | Same handler and launcher |
| Advanced **Replay Browser** | User explicitly chooses any `.jsonl` file | Not applicable: no parent result is claimed | No parent digest exists | File existence at open | Missing is not launched; a valid standalone file remains intentional | Inline browser state, then `open_pygame_client_direct` |
| Development **Open Replay** | Session `_last_test_replay`, derived from the Development Test presentation/result | No click-time result read or identity/association check | No | Existence only when the presentation is loaded; launcher checks existence again | Missing fails at launcher; changed or replaced content launched | `Replay Launch Failed`; `open_pygame_client_direct` |
| Fresh **Evaluation Results** cell | Cached cell artifact directory plus hard-coded `replay.jsonl` | No | No | Existence controls button at selection; no click recheck | A deletion after selection still emitted the stale path; changed or replaced content launched | Launcher failure only; `open_pygame_client_direct` through Designer |
| Fresh **Evaluation Results** comparison row | Candidate cell found by cached `schedule_id`, then the same hard-coded path | No | No | Same as fresh cell | Same as fresh cell | Same common Designer handler and launcher |
| **Evaluation History** cell | Evaluation directory plus recorded cell artifact directory plus hard-coded `replay.jsonl` | Optional deep verification checked result/cell/header association earlier, but opening did not require or repeat it | Only optional deep verification | Existence at selection; no click preflight | Delete/change/replace after selection or after deep verification could bypass the earlier check | Launcher failure only; common Designer handler |
| **Evaluation Comparison** selected left cell | Selected left summary/cell, then hard-coded `replay.jsonl` | No opening-time association check | No | Existence at selection; no click preflight | Delete/change/replace after selection could launch or fail late | Launcher failure only; common Designer handler |
| **Evaluation Comparison** selected right cell | Selected right summary/cell, then hard-coded `replay.jsonl` | No opening-time association check | No | Same as left | Same as left | Same common Designer handler |
| **Evaluation Comparison** one-sided gap cell | The present side's summary/cell, then hard-coded `replay.jsonl` | No opening-time association check | No | Same as left/right | Same as left/right | Same common Designer handler |
| **Replay History** button | Rebuildable index identifies a location; worker re-resolves the canonical contained artifact path | Cached `replay_id`/digest belong to the indexed occurrence; result-backed and replay-only rows have deliberately different guarantees | Recorded digest verified when available | Reconciled at indexing and re-resolved/reverified at click | Missing/unreadable blocks inline; changed blocks with `Replay Changed`; a replaced file fails its recorded digest; legacy replay-only rows without a digest open with an explicit unverified state | Inline status plus one mismatch warning; `open_pygame_client_direct` |
| **Replay History** double-click / Enter | Same selected location and same open signal as its button | Same | Same | Same click worker | Same | Same handler and launcher |
| Immediate **Tournament Results → View Replay** | Tournament record locates a contained match directory; canonical `result.json` supplies filename and digest | Tournament `result_id` is checked when the window loads; replay filename is constrained to the match folder | Recorded digest rechecked at click | Association at load, digest at click | Missing disables/reports unavailable; changed/replaced blocks with `Replay Changed` | Inline missing state or one mismatch warning; `open_pygame_client_direct` |
| **Tournament History → Results → View Replay** | Opens the same `TournamentResultsDialog` over persisted tournament artifacts | Same implementation as immediate results | Same | Same | Same | Same handler and launcher |
| Replay Viewer file picker | User explicitly chooses a `.jsonl` file | Not applicable | No parent digest exists | Replay is parsed by the viewer | Invalid/missing standalone file is a standalone replay-format/file error, not a result-association failure | Replay Viewer itself |
| CLI `bytefray replay --replay PATH` / replay-viewer path argument | Explicit caller-supplied path | Not applicable | No parent digest exists | Replay is parsed by the viewer | Same standalone-file semantics | Canonical replay CLI/viewer |

Revision inspection/restore does not open replays. Evaluation **Test in Agent
Lab** starts a new diagnostic test and opens its trace; it does not open the
persisted evaluation cell replay. Trace Inspector reads `trace.jsonl`, not a
replay. Folder-opening actions likewise are not replay paths.

## 3. Canonical trust model

Canonical `battle2.result` v1/v2 envelopes record `result_id`, `match_id`, and,
when a replay exists, a `replay_id`, portable filename, and SHA-256 digest.
Canonical native replay headers independently record `replay_id`, `match_id`,
`result_id`, and Ruleset identity. The existing `contained_path()` helper
resolves before comparing ancestry and therefore rejects absolute paths,
Windows drive-qualified paths, traversal, and symlink/junction escapes that
resolve outside the expected directory.

The terms used in this phase are:

- **Existence:** the file named by the current canonical result still exists
  as a regular file at click time.
- **Path safety:** the current result's filename resolves inside the expected
  match/cell artifact directory after filesystem resolution.
- **Association:** the current result is the result selected by its parent
  record where that record supplies expected IDs, and its current replay
  reference is the only path considered.
- **Integrity:** the current replay bytes match the SHA-256 in that result.
- **Identity:** the replay header's replay, match, result, and Ruleset IDs agree
  with the current result.

SQLite is never an artifact authority. Replay History may use its rebuildable
index to locate an occurrence and retain the digest observed during indexing,
but an index row cannot override a failed click-time path or digest check.

## 4. Canonical result-associated preflight contract

Immediately before launching a replay on behalf of a recorded result,
Bytefray must:

1. contain and reread the expected `result.json`;
2. when a parent tournament/evaluation record supplies `result_id` or
   `match_id`, compare those expected IDs with the current result;
3. require a well-formed replay reference;
4. resolve the result's current replay filename inside the result's artifact
   directory using canonical containment;
5. require the replay to exist and be readable;
6. verify its bytes against the result's recorded SHA-256;
7. parse a replay header and compare its replay, match, result, and Ruleset
   identities with the result; and
8. launch exactly that verified path only on success.

All eight checks are required for current result-associated native artifacts.
Expected parent IDs are optional only when the calling context genuinely has
no separate parent record. Full association is impossible for a deliberately
standalone replay and for legacy Replay History replay-only records with no
result/digest; those established workflows retain their explicit weaker
guarantee instead of being broken. The artifacts are not cryptographically
signed, so this contract detects ordinary deletion, mutation, substitution,
and inconsistent metadata but is not an authenticity guarantee against an
attacker who coherently rewrites a result, replay, and digest.

## 5. Shared-helper decision

A small Qt-free engine helper is warranted. Evaluation, Tournament, and
session shortcuts all start with a canonical result path, while the existing
digest helper handles only one lower-level integrity dimension. The shared
preflight will compose `read_result`, `contained_path`, canonical digest
verification, and replay-header parsing and return a verified path or a
structured failure category. Qt code will map those categories to the
existing concise `Replay unavailable` / `Replay Changed` vocabulary.

Replay History will retain its deliberately asynchronous, index-aware worker
flow and continue calling the same lower-level canonical digest verifier. A
broad refactor would add risk without improving its applicable click-time
guarantee. Tournament will call the new result-associated preflight rather
than retaining a partial parallel implementation.

## 6. Defects and remediation

### 6.1 Defects confirmed

- Fresh Evaluation Results, Evaluation History, and Evaluation Comparison
  enabled replay actions from a cached hard-coded `replay.jsonl` path. They
  did not reread the cell's `result.json` or verify its digest when the user
  clicked, so a deletion, byte change, or replacement after selection could
  bypass the earlier existence/deep-verification state.
- Simple/Advanced **View Last Match** and Development Test **Open Replay**
  retained a persisted replay path but not the canonical result context used
  to verify it on a later click.
- Tournament correctly checked the tournament-record `result_id` at load and
  the recorded replay digest at click, but its click path retained the result
  fields cached at load. It did not reread the result or independently compare
  replay-header identities at click.
- Tournament's old coarse click outcome would have described a result removed
  after window load as a missing replay. The inline error now distinguishes
  the missing/unreadable verification result from a missing replay file.

### 6.2 Shared implementation

`battle_engine.replay_integrity` adds a Qt-free, non-mutating
`preflight_result_replay()` service. Its `ResultReplayRequest` supplies the
selected result, an expected outer artifact root, and optional parent-record
result/match identities. `ReplayPreflightResult` returns either the exact
verified resolved path or one of these structured failure categories:

- result unavailable or path unsafe;
- result association mismatch;
- replay reference missing or malformed;
- replay path unsafe;
- replay missing, unreadable, changed, or invalid; and
- replay-header identity mismatch.

The service composes existing canonical readers, `contained_path()`, and
`verify_replay_digest()`; it has no Qt, SQLite, or application dependency and
writes nothing. `app.services.replay_integrity` contains only the small request
builder and stable user-facing mapping. Raw exception diagnostics remain in
the structured result for tests/logging and are not displayed by normal GUI
dialogs.

The result path itself must remain beneath the caller's artifact root. The
replay path must remain beneath the result's own directory. Both checks use
fully resolved paths, so ordinary symlink/junction escape follows the existing
`contained_path()` contract. There is no new filesystem-security layer.

### 6.3 Workflow changes

- `EvaluationCellPresentation` now retains the already-recorded cell
  `result_id` and `match_id`. Fresh cells, fresh comparison rows, historical
  cells, comparison left/right selections, and one-sided gaps all emit the
  same `ResultReplayRequest`. One Designer handler performs preflight and only
  then launches. No validation was duplicated in the dialogs.
- Tournament retains its inline missing state and one `Replay Changed` warning
  but now delegates its click check to the shared service, using the
  tournament-record `result_id`. It emits the returned verified path, not the
  path cached when the results window loaded. Immediate and historical
  Tournament Results still use the same dialog.
- Replay History is unchanged. Its index-aware worker continues to re-resolve
  the occurrence and call the canonical lower-level digest verifier on every
  button/double-click/Enter action. This is the correct specialized path for
  indexed result-backed and supported replay-only legacy occurrences; the
  SQLite projection never authorizes a launch.
- Simple/Advanced now retain the last completed match's canonical result path
  beside the replay presentation and use the same preflight at click. A failed
  later run still leaves the prior successful result selected. If that
  recorded result/replay is no longer trusted, Bytefray warns and stops rather
  than flowing into a file chooser as part of the same action. Before any
  session match exists, the established chooser remains a deliberate
  standalone-file workflow.
- Development Test exposes the result path already present in its completed
  presentation and uses it for click-time preflight. Its replay remains
  independent from Simple/Advanced **View Last Match**.
- Advanced Replay Browser, Replay Viewer's picker, and explicit CLI replay
  paths are unchanged. They open intentionally selected standalone replay
  files and do not fabricate a missing parent-result requirement.

### 6.4 Click-time and error behavior

All affected result-backed UI routes construct or evaluate the request in the
click handler. A replay valid at window construction but deleted, modified, or
replaced before the click is refused. A replaced parent result is refused when
the parent evaluation/tournament record supplied an expected identity.

Digest mismatch uses the existing strongest **Replay Changed** explanation.
Missing, unreadable, unsafe, malformed, and association failures use one
succinct **Replay Unavailable** explanation, or Tournament's equivalent inline
state where that avoids modal spam. No failure launches, repairs, regenerates,
rehashes, blesses, migrates, or updates an index.

## 7. Validation and performance

### 7.1 Focused and regression tests

All pytest processes ran sequentially with distinct repo-local `--basetemp`
directories.

| Gate | Result |
|---|---|
| Shared preflight (`engine/tests/test_replay_integrity.py`) | 15 passed, 1 skipped; the skip is Windows test privileges preventing creation of a symlink |
| Evaluation Results + Evaluation History GUI modules | 66 passed offscreen |
| Simple/Advanced View Last Match + Development Test GUI modules | 43 passed offscreen |
| Tournament result service | 20 passed |
| Complete affected Tournament Results/History GUI module | 15 passed offscreen |
| Replay History valid/deleted-after-load/changed-after-load regressions | 3 passed offscreen |
| Advanced standalone Replay Browser handoff | 1 passed offscreen |

The new tests cover valid launch exactly once; deletion and modification after
the UI is loaded; structurally valid wrong replacement; independent replay,
match, result, and Ruleset header-ID mismatches; parent-result substitution;
traversal/drive-qualified replay paths; result-root escape; malformed
references; non-mutation; and a historical result-v1/replay-v3 pair with no
recorded Ruleset field.

### 7.2 Repository gates

- `python -m ruff check .`: passed.
- `python -m mypy engine/src/battle_engine`: passed, 114 source files.
- `python -m mypy client/src/battle_client`: passed, 16 source files.
- Final `python -m pytest`: **3,655 passed, 22 skipped, 3 deselected** in
  377.61 seconds. This is the repository's configured headless suite; GUI
  coverage is reported separately above.

### 7.3 Native and offscreen validation

The Windows session had a real Console desktop and Qt's native `windows`
platform was available. A selected native pytest run covered ten Replay
History, Tournament, fresh Evaluation, Evaluation History, and comparison
valid/missing/changed paths; all ten passed, although Qt/Windows emitted a
recoverable COM diagnostic (`0x8001010d`) while Replay History's worker event
loop was being pumped. That noisy run was not treated as the sole native
evidence.

A separate native, non-pytest visual smoke used isolated canonical match
artifacts under `.pytest-tmp`, showed the real Evaluation Results, Tournament
Results, and Replay History windows, and intercepted only the final Viewer
process spawn. Visual inspection of native screenshots confirmed the valid
selected states and concise warnings. Each valid action produced exactly one
handoff; modifying the replay after its window was open produced no second
handoff and showed **Replay Changed** in all three workflows. Replay History's
inline status also changed to `Replay file is no longer available.` The smoke
reported Qt platform `windows`, exited cleanly, closed its history worker and
windows, and its temporary artifacts/screenshots were removed afterward.

The affected GUI tests also ran offscreen with every expected modal
intercepted and unexpected critical dialogs configured to fail rather than
block. No real Replay Viewer was spawned during automated or visual
qualification.

### 7.4 Performance

An isolated native-match probe measured the complete synchronous preflight 25
times at each normal Simple tick preset:

| Ticks | Replay size | Median complete preflight |
|---:|---:|---:|
| 300 | 173,056 bytes | 1.28 ms |
| 600 | 342,656 bytes | 1.41 ms |
| 1,200 | 683,381 bytes | 1.46 ms |

This includes result read, SHA-256, header parse, and identity comparison. No
actual GUI stall was observed, so one synchronous check per explicit open is
the appropriate scope; asynchronous hashing is deferred unless a real large
artifact demonstrates a usability problem.

### 7.5 Historical compatibility

Result-associated native artifacts begin with `battle2.result` v1 and
`battle2.replay` v3; those released pairs carry replay/match/result identities.
Ruleset identity was added later to both records and may legitimately be
absent on both. Direct `None == None` association preserves that valid case,
and a focused v1/v3 missing-Ruleset test passes. Current schema-4 native
replays require recorded identity. pMARS results legitimately have no replay
reference and remain browseable but not replay-openable.

Replay History's older replay-only formats may lack a result and digest. They
retain its existing explicit `UNVERIFIED_LEGACY` behavior; the phase does not
invent metadata, migrate artifacts, or break intentional standalone replay
support.

## 8. Deferred boundaries

- The final few filesystem operations cannot be made atomic with a detached
  Replay Viewer process without changing the viewer handoff/API. Verification
  is therefore performed immediately before launch, which closes the stale
  window that motivated this phase but cannot prevent a file change in the
  instant after preflight.
- Standalone replay parsing has no parent result or digest to consult.
- Replay History's supported legacy replay-only rows cannot gain association
  metadata that their artifacts never recorded.
- No asynchronous hashing infrastructure is introduced unless measurement
  demonstrates an actual usability problem.

## 9. Final tree state

HEAD remains the unmodified Phase 5 commit. Phase 6 is intentionally present
only as uncommitted source, test, and this research-report work. Final status,
diff, process, and lock evidence is recorded in the completion report.
