# Bytefray V5 — Phase 7E: Final Qualification

Phase 7E implemented the concurrent-reader architecture Phase 7C and 7D both
deferred and recommended (Phase 7D Section T): a second, read-only
`ReplayHistoryService` on its own `QThread`, opened against the prepared
SQLite cache with `mode=ro`, so `resolve_replay`, `verify_replay_integrity`,
`fetchDetail`, and page/count reads no longer queue behind an active
maintenance refresh on the single worker Phase 7C/7D shared. This document
does not redesign or re-implement that architecture — it is the final
qualification pass this session was asked to run against the work already
present in the working tree: one clean canonical full-suite run, a rerun of
the permanent Ruleset 4 equivalence suite, integrity verification of the
qualified tree, a full diff review, and the explicit prerelease-readiness
decision.

---

## A. Starting state

| Item | Observed value |
|---|---|
| Branch | `v5-research` |
| Exact HEAD | `c265fddc5e703108c5de199977eedda8b6ffd02a` (Phase 7B commit, 2026-09-11T20:31:09-04:00) |
| Upstream | `origin/v5-research`, 0 ahead / 0 behind |
| Bytefray version | `5.0.0a1` (unchanged) |
| Working tree at start of this session | **Not clean.** Phases 7C, 7D, and 7E's implementation, recovery/lifecycle stress tests, visual review, and focused qualification were already present as uncommitted work, exactly as listed in Section K below. No prior HEAD advanced past 7B during 7C/7D/7E. |
| No other pytest process running | Confirmed (`Get-Process` for `python`/`pytest` returned nothing) before this session's runs began |

This session did not implement, redesign, or modify the concurrent-reader
architecture, the GUI, or the backend. It ran verification only.

---

## B. What this session verified first-hand vs. what it carries forward

Per the qualification-tier discipline this project's phase reports follow,
this section states plainly what was newly, independently observed in this
session versus what is carried forward from work already completed earlier
in Phase 7E, so that neither is misrepresented as the other.

**Verified first-hand, this session, against the exact working tree described
in Section A/G:**

* No other pytest process was running before either run started.
* Permanent Ruleset 4 equivalence: `engine/tests/test_v4_stable_ruleset_equivalence.py`
  (Section D).
* One clean canonical full-suite run (Section E).
* `ruff check .` and both `mypy` invocations, reconfirmed against the current
  tree (Section D).
* `git diff --check` and `git status --short` (Section F).
* A full read of every diff hunk and every new file's relevant surface
  (Section H).
* Working-tree integrity across both long-running commands via SHA-256
  hashes of every changed file, taken before and after (Section G).

**Carried forward, not re-executed this session, per the explicit instruction
not to redo completed work:** the concurrent-reader implementation itself,
the recovery/lifecycle stress tests, the visual/manual review, the prior
focused qualification pass, and the display-backed GUI suite. This session
has no independent run output for the GUI suite's pass count in this exact
Phase 7E state and does not restate one; the last figure this document's
lineage can attest to first-hand is Phase 7D's own recorded **422 passed, 6
deselected** (`pytest tests/ -m gui`), which predates Phase 7E's additions to
`tests/test_v5_replay_history_browser.py` and the new
`tests/test_v5_replay_history_qualification.py`. Reporting a Phase-7E-current
GUI-suite number here would be presenting an unreproduced figure as if
observed, which is exactly what this project's evidence standard rules out.
If a current figure is needed, it must come from an actual run.

---

## C. Scope discipline

No feature work, no performance redesign, and no architectural change was
made in this session. Confirmed by the hash comparison in Section G: every
file that carries Phase 7C/7D/7E's changes is byte-identical before and
after both the Ruleset 4 rerun and the full-suite run.

---

## D. Ruleset 4 permanent equivalence, Ruff, mypy

| Check | Result |
|---|---|
| `pytest engine/tests/test_v4_stable_ruleset_equivalence.py -v` | **23 passed** in 28.42s — identical count to Phase 7D's own recorded 23; rerun in this session specifically because the task required confirming it runs clean after the final lifecycle fixes, and this session had no prior evidence that it had been |
| `ruff check .` | **All checks passed** |
| `mypy engine/src/battle_engine` | **Success: no issues found in 113 source files** |
| `mypy client/src/battle_client` | **Success: no issues found in 16 source files** |

`app/` (the PySide6 Designer, including `app/views/replay_history.py` and
`app/services/replay_history_presentation.py`) is not covered by either
`mypy` invocation, consistent with `AGENTS.md`'s testing expectations and
every prior phase report in this series.

---

## E. Canonical full suite

One run, `python -m pytest` (default `testpaths`: `_legacy/tests`,
`engine/tests`, `client/tests` — the true repository suite, not
`engine/tests/` alone):

```
3612 passed, 21 skipped, 3 deselected in 352.80s (0:05:52)
```

**No failures.** This is a clean result on the first and only attempt this
session made — unlike Phase 7D, which saw 3 spurious failures caused by an
overlapping second pytest process against a shared `--basetemp`, this run
was confirmed to be the sole pytest invocation for its entire duration
(Section A).

**Test-count reconciliation against Phase 7D's own recorded full-suite run**
(`3,589 passed, 3 failed, 21 skipped, 3 deselected` = 3,616 collected):
this run collected 3,636 tests, exactly 20 more. `engine/tests/test_replay_history_concurrency.py`
— new in Phase 7E, inside `testpaths` — collects exactly 20 tests. No other
file inside `testpaths` changed its collected count between the two runs.
The entire growth is accounted for by that one new file; nothing
uncollected or over-collected.

`tests/test_v5_replay_history_qualification.py` (10 tests, `gui`-marked) and
the 7 tests Phase 7E added to `tests/test_v5_replay_history_browser.py` (84
→ 91) live under root `tests/`, which is outside `pytest.ini`'s `testpaths`
and therefore correctly absent from this canonical run — they belong to the
GUI suite (Section B).

---

## F. Full-rebuild performance discrepancy — preserved as measured, not re-diagnosed

This is carried forward exactly as reported earlier in Phase 7E, because
this session was explicitly instructed to preserve it rather than
re-attribute it:

| Measurement | Value | Session |
|---|---:|---|
| Full corpus rebuild (real 53,458-occurrence corpus) | **~26 s** (26.06 s, 25.6–28.0 s across five runs) | Phase 7B |
| Full corpus rebuild, same corpus class | **279 s** (cold, one measurement) | Phase 7D |
| Full corpus rebuild, before this phase's optimization work | **~273 s** | Phase 7E |
| Full corpus rebuild, after this phase's optimization work | **~268.8 s** | Phase 7E |
| Warm reconcile, no changes | **~7.5–8 s** (7.36–8.5 s across phases) | Phase 7B/7C, unchanged in 7E |
| Concurrent read interactions (`resolve_replay`, `verify_replay_integrity`, page/count/detail reads against a live reader) | Sub-second; generally millisecond-scale | Phase 7E |

**This session did not re-measure the full-rebuild figure and did not
attempt to diagnose it further** — doing so was not in this session's scope,
and the task's own instruction was explicit: do not attribute this
discrepancy to the concurrent-reader change without evidence. The evidence
actually available points the other way:

* The regression **predates** Phase 7E entirely. Phase 7D — which added no
  filesystem-scan or SQL logic and made no concurrency change — already
  observed the identical class of slowdown on this machine (its own Section
  M records a cold-rebuild attempt "extrapolated... on the order of hours,"
  against Phase 7C's own 279 s baseline on the same corpus), and explicitly
  characterized it as "session/environment variance... rather than anything
  [that phase] changed."
* Phase 7E's own before/after figures (~273 s → ~268.8 s, a ~1.7% change)
  are far too close together to constitute evidence that the concurrent-reader
  work — which touches the *read* path, not the rebuild/write path — caused
  or fixed a 10×-scale regression from Phase 7B's 26 s. A change to the read
  path would not be expected to move the write-side rebuild duration at all;
  the small before/after delta is consistent with ordinary run-to-run
  variance on an already I/O-bound operation, not a causal effect of
  anything Phase 7E implemented.
* The warm-reconcile figure — the operation that actually runs during normal
  product use — remains stable at ~7.5–8 s across Phase 7B, 7C, and 7E,
  unaffected by whatever is driving the full-rebuild number. A full rebuild
  only occurs on first open or cache loss (Section I of Phase 7B), so this
  discrepancy, however large, does not change the qualification verdict for
  the concurrent-reader work itself, which is what Phase 7E's tests
  characterize (Section D of this document; `engine/tests/test_replay_history_concurrency.py`
  and `tests/test_v5_replay_history_qualification.py`).

The honest state of this finding is: a real, large, environment-linked
full-rebuild slowdown exists on this machine, first observed in Phase 7D
before any concurrent-reader code existed, and persists through Phase 7E
almost unchanged by that phase's optimization attempt. Its root cause is
**not determined** by any evidence collected in Phase 7D or Phase 7E, and it
should not be reported as resolved, as a regression caused by this phase, or
as improved by this phase's ~1.7% delta.

---

## G. Working-tree integrity protocol

Per this repository's qualification-integrity requirement that the exact
code qualified is the exact code preserved, SHA-256 digests of all 19
modified/untracked files carrying Phase 7C/7D/7E's changes were taken
immediately before the Ruleset 4 rerun and recomputed immediately after the
full-suite run:

* **HEAD before:** `c265fddc5e703108c5de199977eedda8b6ffd02a`
* **HEAD after:** `c265fddc5e703108c5de199977eedda8b6ffd02a` — unchanged
* **`git status --short` before and after:** identical, byte-for-byte the
  same 19-entry list (Section A)
* **File hashes:** all 19 files matched exactly, before vs. after — **"ALL
  HASHES MATCH (19 files)"**

No mutation occurred during either run. The suite that passed and the tree
now under review are provably the same code.

---

## H. `git diff --check` and `git status`

```
git diff --check
```
Exit code 0. Only pre-existing CRLF-normalization notices on files that were
already CRLF in the working copy (`ARCHITECTURE.md`, `README.md`,
`app/agent_designer.py`, `docs/MANUAL_SMOKE_TESTS.md`, the four
`replay_history/*.py` backend modules, `engine/tests/test_replay_reconstruction.py`)
— the same class of notice Phase 7D recorded, not a new whitespace error.

```
git status --short
```
Matches Section A/K exactly. No run artifact, cache file, screenshot, or
`.pytest-tmp`/`.pytest-cache` content is tracked.

---

## I. Diff review for unintended changes

The complete diff was read in full: every hunk of all 11 modified tracked
files, plus the relevant surface of all 8 new untracked files (backend
`query.py`/`index.py`/`service.py`/`__init__.py` additions; the GUI's
two-`QThread` wiring in `app/views/replay_history.py`; `app/agent_designer.py`'s
shutdown-ordering change; and all four new/changed test modules).

**Findings: none.** Specifically checked and confirmed absent:

* No gameplay, Ruleset, schema (`battle2.result`/`battle2.replay`), or Agent
  API semantic change anywhere in the diff.
* No SQL/database access, `result.json`/replay parsing, or Viewer-command
  construction inside `app/views/replay_history.py` or
  `app/services/replay_history_presentation.py` — both remain Qt-free of
  history semantics and read only already-normalized backend values, exactly
  as ARCHITECTURE.md's Phase 7E addition states.
* `result_model.verify_replay_digest`'s extraction into
  `verify_replay_digest_value` remains a pure, behavior-preserving refactor;
  both are exercised and both pass (Section E).
* No debug leftovers (`TODO`/`FIXME`/`print(`/`pdb.set_trace`/`breakpoint()`)
  in any changed or new file. (An automated grep hit on "print(" was a
  substring match inside `ArtifactFingerprint(` — a real constructor call,
  not a debug statement — verified by inspection.)
* The new `HistoryIndex.open_read_only` / `ReplayHistoryService(..., read_only=True)`
  path raises `PermissionError` from every mutating entry point
  (`refresh`/`rebuild`/`reconcile`, `write_transaction`) and opens the
  connection with `PRAGMA query_only = ON` plus SQLite's own `mode=ro` URI
  flag — a double-enforced read-only boundary, both proven directly by
  `engine/tests/test_replay_history_concurrency.py::test_read_only_service_rejects_maintenance_and_sql_writes`.
* The reader never creates, recovers, or relabels a missing/damaged cache —
  `open_read_only` raises rather than falling back to `HistoryIndex.open`'s
  create/recover path, proven by
  `test_reader_never_recovers_or_relabels_invalid_cache` across all four
  damage modes (`bytes`/`version`/`metadata`/`root`), each asserting the
  on-disk cache bytes are unchanged after the failed open.
* `app/agent_designer.py`'s `closeEvent` joins the Replay History worker(s)
  before its own children are destroyed — a shutdown-ordering fix, not a
  behavior change to any other Designer flow; nothing else in that file's
  diff touches match execution, evaluation, or catalog code.
* No new file, anywhere in the diff, appears under `runs/`, `.pytest-tmp/`,
  `.pytest-cache/`, or any other artifact/cache path.

Confirmed unchanged (same standing as every prior phase in this series):
result schema, replay schema, `match_id`, SQLite occurrence/entrant schema
beyond the additive `winner_display_name` projection and `RulesetFacet`
query (both already reported and tested in Phase 7C/7D lineage), Designer
match behavior, CLI behavior, gameplay, Rulesets, and product version.

---

## J. Files changed (cumulative Phase 7C + 7D + 7E, still uncommitted)

**Modified**

| File | Phase(s) |
|---|---|
| `ARCHITECTURE.md` | 7C, 7D, 7E (two-worker architecture section) |
| `README.md` | 7C, 7D |
| `app/agent_designer.py` | 7C (menu wiring), 7E (reader-aware shutdown ordering) |
| `docs/MANUAL_SMOKE_TESTS.md` | 7C, 7D |
| `engine/src/battle_engine/replay_history/__init__.py` | 7D, 7E exports |
| `engine/src/battle_engine/replay_history/index.py` | 7C (`ruleset_facets`), 7E (`open_read_only`, `read_snapshot`, winner-name subquery) |
| `engine/src/battle_engine/replay_history/query.py` | 7D (integrity types), 7C (`RulesetFacet`), 7E (`winner_display_name`) |
| `engine/src/battle_engine/replay_history/service.py` | 7D (`verify_replay_integrity`), 7E (`read_only`, `fetch_page_with_count`, `_require_writer`, cancellation checks) |
| `engine/src/battle_engine/result_model.py` | 7D (`verify_replay_digest_value` extraction) |
| `engine/tests/test_replay_history.py` | 7D (integrity tests) |
| `engine/tests/test_replay_reconstruction.py` | 7D (`verify_replay_digest_value` unit tests) |

**Added (untracked)**

| File | Phase(s) |
|---|---|
| `app/services/replay_history_presentation.py` | 7C, 7D |
| `app/views/replay_history.py` | 7C, 7D, 7E (second reader `QThread`) |
| `docs/research/v5/V5_REPLAY_HISTORY_PHASE7C_BROWSER_UI.md` | 7C's own report |
| `docs/research/v5/V5_REPLAY_HISTORY_PHASE7D_VIEWER_HANDOFF.md` | 7D's own report |
| `engine/tests/test_replay_history_concurrency.py` | 7E (new, 20 tests) |
| `engine/tests/test_v5_replay_history_presentation.py` | 7C, 7D |
| `tests/test_v5_replay_history_browser.py` | 7C, 7D, 7E (grew 84 → 91) |
| `tests/test_v5_replay_history_qualification.py` | 7E (new, 10 `gui`-marked tests) |

This document (`V5_REPLAY_HISTORY_PHASE7E_FINAL_QUALIFICATION.md`) is added
by this session and is not yet part of the tree hashed in Section G, since
it is this qualification's own output rather than qualified input.

---

## K. Explicit confirmations

1. No other pytest process was running before this session's runs began.
2. Permanent Ruleset 4 equivalence passes after the final lifecycle fixes:
   23/23, rerun in this session (Section D).
3. One clean canonical full-suite run: 3,612 passed, 21 skipped, 3
   deselected, **zero failures** (Section E).
4. `ruff check .` and both `mypy` invocations pass against the current tree,
   reconfirmed this session (Section D).
5. `git diff --check` is clean; `git status --short` matches the documented
   file list exactly (Section H).
6. HEAD and every changed file's SHA-256 digest are unchanged from before
   the qualification runs to after (Section G) — the qualified tree is
   provably the tree that was tested.
7. The complete diff was reviewed in full; no unintended change was found
   (Section I).
8. The full-rebuild performance figures (~273 s / ~268.8 s Phase 7E vs. ~26 s
   Phase 7B) are preserved as measured and are **not** attributed to the
   concurrent-reader change without evidence; the available evidence points
   to a pre-existing environment/session characteristic first observed in
   Phase 7D (Section F).
9. Result and replay schemas, SQLite core schema, gameplay, Rulesets, CLI
   semantics, and product version are unchanged.
10. No commit and no push were performed by this session.

---

## L. Prerelease-readiness decision

Applying this repository's four-tier qualification framework:

1. **Source qualification — PASS.** Automated suites (canonical full suite,
   Ruleset 4 permanent equivalence, and — carried forward, not re-executed —
   the GUI suite and prior focused qualification), `ruff`, and `mypy` all
   pass against a committed-equivalent, hash-verified, unmodified working
   tree.
2. **Packaged qualification — NOT REACHED.** No Windows installer, portable
   ZIP, wheel, or source archive was built or tested from this tree in this
   session. This is unchanged from every prior Replay History phase and
   remains a gate before this feature ships in any built alpha.
3. **Interactive first-user qualification — NOT REACHED.** This is a
   non-interactive session; no human drove an installed application, clicked
   a Start Menu shortcut, or observed a real Pygame window. The interactive
   checklist Phase 7D added to `docs/MANUAL_SMOKE_TESTS.md` (items 13–20)
   remains the required path for this tier and has not been executed here.
4. **Publication — NOT REACHED and not in scope.** No tag, merge, or GitHub
   release is implicated by this phase.

**Decision: Phase 7E's concurrent-reader architecture is qualified complete
at the source-qualification tier and is ready to commit as-is.** The
canonical full suite is clean with zero failures on an isolated, hash-verified
run; the permanent Ruleset 4 equivalence gate holds; static analysis is
clean; and a full diff review found no unintended change. This is a
successful outcome for what this session was asked to establish.

This decision does **not** extend to packaged or interactive qualification,
which this session neither attempted nor can attempt, and it does **not**
resolve the full-rebuild performance discrepancy (Section F), which is
carried forward as an open, evidence-bounded finding rather than closed out.
Committing this work is a decision for the user; this session performed no
commit and no push.
