# V5 Alpha 1 Phase 4 — Tournament UX Completion

Scope: complete and qualify the Designer workflow **Configure → Run
Tournament → See Results → Browse Matches → View Replay** without changing
tournament scheduling, gameplay, scoring, persistence, or replay semantics.

The architecture gate classified the repository as **Case A**: durable,
canonical tournament results already existed, and the missing capability was
presentation and navigation. No new tournament schema, index, database, or
replay format was introduced.

## 1. Baseline, takeover, and process safety

Phase 4 began from branch `v5-research` at
`880e0b6867fdf40a5dd28ca50d5392e58c2eff54` (`V5 Alpha1 Phase 3 changes`).
The earlier implementation session recorded a clean tree before editing and
left the implementation uncommitted.

Codex took over on 2026-09-13 with the same branch and HEAD. The tree contained
exactly the expected Phase 4 paths:

- modified: `ARCHITECTURE.md`, `app/agent_designer.py`,
  `app/views/tournament.py`, `docs/MANUAL_SMOKE_TESTS.md`,
  `docs/TOURNAMENTS.md`, and
  `tests/test_v5_alpha1_phase2_menu_organization.py`;
- untracked: `app/services/tournament_results.py`,
  `engine/tests/test_tournament_results.py`, and
  `tests/test_v5_alpha1_phase4_tournament_results.py`.

No Python, pytest, tournament, or replay-viewer process was active. The only
matching processes were VS Code's Codex/Claude agent servers; file hashes and
Git state showed no concurrent writer. The nine implementation/test/doc files
were byte-identical to the earlier pre-full-suite snapshot.

## 2. Architecture audit and Case A decision

The supported path is:

1. Designer **Tools → Run Tournament…** opens `TournamentDialog`.
2. `build_designer_tournament_command` delegates to the engine launcher.
3. `bytefray tournament` runs `TournamentService` over the normal native match
   service.
4. The service atomically checkpoints `tournament.json` after each recorded
   match and writes final standings after the schedule finishes.
5. Every completed native match writes the normal canonical `result.json` and
   `replay.jsonl` pair.

The canonical artifact tree is:

```text
tournament.json                                  battle2.tournament v1
matches/<scheduled-match>/result.json            canonical match result
matches/<scheduled-match>/replay.jsonl           canonical normal replay
```

`tournament.json` already provides the tournament ID, division, ordered match
records, match status and artifact folders, and final standings. Each
completed match's `result.json` provides the winner, names, termination,
Ruleset, and digest-bearing replay reference. The replay is an ordinary
Bytefray replay and opens through the existing Replay Viewer.

This is sufficient to reconstruct the requested results experience after a
restart. Therefore Phase 4 is **Case A**: add a read-only presentation layer,
not another persistence layer. `tournament.json` remains the central
machine-readable tournament artifact, with each `result.json` remaining the
canonical match result.

## 3. Pre-existing defects

| ID | Finding | Phase 4 resolution |
|---|---|---|
| D1 | Designer always proposed `runs/tournaments/designer-tournament`. A later request with a different roster/config collided with the earlier state and was rejected. | Every launch proposes a fresh `designer-<UTC timestamp>-<suffix>` directory. Explicitly choosing an existing compatible folder still preserves resume semantics. |
| D2 | After a subprocess failed without writing state, Designer could read the folder's old `tournament.json` and present it as the new result. | Record the pre-launch state signature and show **Tournament Did Not Run** when it is unchanged. Earlier results are explicitly left unpresented as the current run. |
| D3 | Stop logged `[RunMatch] stopped.` for tournaments. | Tournament Stop logs `[Tournament] stopped.` |
| D4 | Tournament documentation put **Open Last Output Folder** under Tools. | Documentation now correctly identifies **File → Open Last Output Folder**. |

No tournament-engine, scoring, or replay defect was found.

## 4. Qt-free results and history reader

`app/services/tournament_results.py` is read-only and imports no Qt modules. It:

- accepts only `battle2.tournament` version 1 and validates its required
  structures;
- recognizes completion from the service's existing write contract: final
  standings are written only after the schedule loop finishes;
- reproduces the service's ordering basis (wins, then score), adds competition
  ranks, and presents equal wins and score as a shared rank/tie rather than
  treating agent-ID row ordering as a competitive tiebreak;
- distinguishes winner, leader in a completed tournament with match errors,
  tied leaders, no completed matches, and an interrupted tournament;
- resolves recorded match folders only within the tournament root, normalizes
  Windows/POSIX separators, and rejects containment escapes;
- reads completed matches through the canonical result reader and requires the
  result ID to match the tournament record;
- accepts only a bare replay filename in the match folder, reports a missing
  replay inline, and rechecks its recorded SHA-256 immediately before opening;
- discovers direct child tournament folders beneath
  `<data-root>/runs/tournaments`, newest state mtime first, while retaining
  damaged entries as visibly unreadable;
- provides fresh Designer output paths, state signatures, and bounded useful
  subprocess-error text for a run that wrote nothing.

The reader does not duplicate tournament scheduling, scoring, replay parsing,
or replay-viewer logic and does not write or repair artifacts.

## 5. Tournament Results and History UI

`TournamentDialog` remains functionally unchanged apart from receiving the new
fresh default output path.

`TournamentResultsDialog` presents:

- winner/leader/tie/no-winner headline and completion explanation;
- recorded Ruleset when readable, runtime/entrant count, match count, and
  output folder;
- read-only standings with shared ranks and W/L/T/score;
- the ordered match list, selection-driven detail, and clear replay
  availability;
- **View Replay**, including double-click, after click-time digest verification;
- **Open Output Folder**.

`TournamentHistoryDialog` presents direct-child saved tournaments newest first,
including complete, error-complete, interrupted, and unreadable states. It
supports **View Results**, double-click, **Open Tournament Folder…** for an
external folder, and **Refresh**. A nested Results dialog forwards replay
requests to the Designer's existing normal replay-opening handler.

Independent review found the dialog ownership and lifetime sane: modal dialogs
are parented and retained through `exec()`, nested Results dialogs are parented
to History, and signal forwarding does not create another viewer. Selection
changes consistently enable/disable actions; double-click cannot bypass an
unavailable replay; tables are read-only, resize columns, retain tooltips, and
scroll; long paths wrap or remain selectable. No unexpected modal loop or
blocking path was found.

## 6. Designer integration and final workflow

`app/agent_designer.py` now:

- adds **Tournament History…** beside **Run Tournament…** in Tools;
- proposes a fresh output folder per launch;
- records the pre-launch `tournament.json` signature and buffers tournament
  stderr;
- refuses to present unchanged earlier state as the current result;
- automatically opens Results for newly recorded complete or partial state;
- opens a selected replay through the existing
  `open_pygame_client_direct` path;
- logs the correct tournament Stop label.

The resulting workflow is:

1. **Tools → Run Tournament…**
2. configure entrants and Run
3. **Tournament Results** opens automatically
4. inspect status, standings, and matches
5. select a completed match and **View Replay**
6. the normal Replay Viewer opens while Results remains available
7. later, **Tools → Tournament History… → View Results** reopens the same
   canonical artifacts and their constituent replays.

There is no redundant success dialog between completion and Results, and
filesystem navigation is optional.

## 7. Partial, failure, and integrity behavior

| Situation | Presentation |
|---|---|
| Invalid request or incompatible unchanged output folder | **Tournament Did Not Run**, useful CLI stderr, exit code, and no stale results dialog |
| Some matches failed/rejected/corrupted | Tournament is finished with errors; the top row is a leader, standings count only completed matches, and failed rows retain their status/error |
| No matches completed | No winner |
| Process stopped/killed after checkpoints | Tournament did not finish; no final standings; recorded matches remain reachable through History |
| Result missing/damaged or identity mismatch | Match result and replay are unavailable; foreign data is not presented as that match |
| Replay missing | Inline unavailable reason; no launch |
| Replay changed after loading | **Replay Changed** warning; no launch |
| Output folder missing after display | Folder action reports that it no longer exists |

Resume/retry behavior in `TournamentService` and the CLI is unchanged.

## 8. Tournament History and central-artifact decisions

History is deliberately an index-free, synchronous view over existing
`tournament.json` files. It creates no cache, manifest, summary, database, or
additional artifact. A tournament outside the normal root remains available
through **Open Tournament Folder…**.

No `battle2.tournament` version 2 decision was made. Historical v1 outputs are
read without migration or rewriting.

## 9. Open Last Output Folder

The existing Designer handler and priority chain are unchanged. After a
tournament launch, **File → Open Last Output Folder** points to the same folder
as Results' **Open Output Folder**. Because the proposed directory is fresh per
launch, it identifies the most recently launched tournament instead of a shared
fixed folder.

## 10. Tests added and changed

Added `engine/tests/test_tournament_results.py` (19 headless tests), using real
`TournamentService` artifacts to cover canonical values, rankings and ties,
partial/interrupted/no-completion states, missing/changed replays, mismatched
result identity, path containment and separator normalization, damaged or
unsupported state, history ordering, signatures, not-run reporting, and fresh
output directories.

Added `tests/test_v5_alpha1_phase4_tournament_results.py` (14 GUI tests), with
message-box guards that record every modal instead of allowing an unexpected
headless `exec()` to hang. It covers Results, History, replay handoff, replay
failure paths, stale-state protection, fresh folders, output-folder targets,
menu/wiring, Stop labeling, and a real Designer-launched
`bytefray tournament` subprocess.

Updated `tests/test_v5_alpha1_phase2_menu_organization.py` to pin the current
Tools menu contract and Tournament History wiring. No existing guard was
weakened.

## 11. Qualification results

All runs were sequential. The implementation/test/doc files were byte-identical
to the pre-full-suite snapshot when Codex took over, so the earlier broad-suite
evidence remains applicable. Codex freshly repeated both Phase 4 focused runs.

| Qualification | Result | Evidence source |
|---|---|---|
| `engine/tests/test_tournament_results.py` | **19 passed in 1.08s** | fresh Codex run |
| `tests/test_v5_alpha1_phase4_tournament_results.py -m gui` | **14 passed in 2.71s** | fresh Codex run, offscreen Qt |
| affected existing GUI regressions | **157 passed** | earlier successful run; hashes unchanged |
| tournament/replay headless regressions | **256 passed, 1 skipped** | earlier successful run; hashes unchanged |
| canonical GUI suite `pytest tests/ -m gui` | **PASS**; 489 selected of 495 collected, 6 deselected | earlier successful run; hashes unchanged |
| canonical full suite `python -m pytest` | **3639 passed, 21 skipped, 3 deselected** in 356.43s | preserved log with exit 0; hashes unchanged |
| `ruff check .` | **All checks passed** | earlier successful run; hashes unchanged |
| `mypy engine/src/battle_engine` | **Success: no issues in 113 source files** | earlier successful run; hashes unchanged |
| `mypy client/src/battle_client` | **Success: no issues in 16 source files** | earlier successful run; hashes unchanged |

The stored full-suite metadata records start `2026-09-13T11:44:49-04:00`, end
`11:50:46-04:00`, exit 0, and elapsed 357.14 seconds. Post-suite and takeover
hash comparison covered all nine critical implementation/test/doc files.

## 12. Native Windows sighted validation

Codex ran the corrected scratch drive on the native Qt `windows` platform and
visually inspected all nine captured PNGs. The drive used the real Designer,
real tournament subprocess, real canonical artifacts, and normal replay-viewer
launch path.

Verified:

- the Tools action order was **Run Tournament…**, **Tournament History…**,
  separator, **Evaluation History…**, **Replay History…**;
- a three-agent tournament proposed a fresh output folder and completed;
- Results opened automatically with `Winner: Seeker (Starter)`, Ruleset v1,
  three entrants, three completed matches, coherent standings, and usable
  match rows/details;
- View Replay launched `battle_client.cli --renderer pygame`; the process was
  still alive after six seconds and Results remained open;
- Results and File output-folder actions targeted the identical tournament
  root;
- a different roster forced into the first folder produced the clear
  **Tournament Did Not Run** warning and opened no stale Results dialog;
- Stop logged `[Tournament] stopped.` and opened no result modal;
- History listed the finished and stopped tournaments newest first, reopened
  both, and the stopped result claimed no winner, showed no final standings,
  and opened on Matches;
- screenshots showed no clipping that hid an action or value, broken sizing,
  unusable table, modal loop, or confusing dead end. Long paths wrapped, and
  large match sets scrolled.

The scratch harness reached and logged every planned checkpoint, closed the
dialogs, and left no Python/replay process. Its wrapper nevertheless returned a
nonzero status after the last window closed: Qt's default
quit-on-last-window behavior returned from `qt_app.exec()`, and the scratch
script then fell through to its own `finish(3)` line before the already-scheduled
`finish(0)` timer could run. This is a scratch finalization defect, not a
Bytefray product failure; the product verdict uses the completed structured log,
captured screenshots, live replay-process observation, and clean process check.

**Native Windows sighted result: PASS, with the scratch exit-code caveat above.**

## 13. Documentation

`ARCHITECTURE.md` identifies the Qt-free result reader and canonical-artifact
presentation boundary. `docs/TOURNAMENTS.md` documents fresh Designer folders,
automatic Results, integrity behavior, History, and the correct File-menu
location. `docs/MANUAL_SMOKE_TESTS.md` contains the packaged interactive
workflow. No unrelated documentation cleanup was performed.

The checkout emits the pre-existing CRLF/LF warnings for `ARCHITECTURE.md` and
`docs/MANUAL_SMOKE_TESTS.md`; the diffs are focused rather than whole-file
line-ending rewrites, and `git diff --check` reports no whitespace error.

## 14. Deferred items

- Tournament-level timestamp, Ruleset, seed, rounds, tick limit/config, and
  entrant display names are not persisted. Adding them requires an explicit
  future `battle2.tournament` schema decision.
- Very large History/result sets may eventually need background loading.
- Tournament History and Replay History are not cross-linked.
- CLI default-folder resume semantics are unchanged.
- The generic replay-open handler retains its evaluation-specific method name.
- Per-entrant match scores are not shown in match detail.

These are not Phase 4 blockers and were not pulled into this change.

## 15. Final integrity and recommendation

Codex made no production or test correction; the only Codex repository change
is this reconciled report. Final HEAD remains
`880e0b6867fdf40a5dd28ca50d5392e58c2eff54`. The original six modified and
three untracked implementation/test paths remain uncommitted, and this report
is the additional untracked path. No file was staged, stashed, reset, restored,
committed, or pushed.

No Python, pytest, tournament, or replay-viewer process remains. The Phase 4
implementation is **ready to commit** as one reviewed change, subject to the
operator's normal diff/staging review. Publication is outside this phase and
was not performed.
