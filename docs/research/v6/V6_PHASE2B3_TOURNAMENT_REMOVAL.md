# Bytefray V6 Research — Phase 2B.3: Remove Obsolete Tournament Harness

**Status:** Phase 2B.3 — implementation of the Phase 2B.2 REMOVE disposition.
The obsolete root-level `tournament/` developer harness and its dedicated test
file have been deleted from the working tree. No commit was made per the
phase charter (§18); the removal is left staged/unstaged for review.

---

## A. Baseline

| Check | Result |
|---|---|
| Branch | `v6-research` |
| HEAD SHA at phase start | `5f7f1886495f52b732301d1955424c79a25a746e` ("Bytefray V6 Phase 2B.2 — Tournament Pipeline Disposition Research" — the Phase 2B.2 report commit itself; no commits were added between Phase 2B.2's close and this phase's start) |
| Phase 2B.2 committed | Yes — it **is** HEAD |
| Working tree at start | Clean (`git status --porcelain` empty) |
| `origin/v6-research` divergence | None — `git fetch --all --prune` then `git status -sb` reports `## v6-research...origin/v6-research` with no ahead/behind; `git rev-parse origin/v6-research` == HEAD |
| `main` | Untouched — `git rev-parse main` == `git rev-parse origin/main` == `82549f9c3ccbdb2e13b8165b32afef00def4a8f2`, identical to every prior phase's recorded value |
| Starting canonical test count | **3,741 collected** (`python -m pytest --collect-only -q`, per-file counts summed) — reconciles exactly with Phase 2B.2's closing count |

---

## B. Disposition confirmation

Because HEAD at phase start **is** the Phase 2B.2 commit, there is a zero-commit
delta to re-check for new dependencies — nothing landed on this branch between
the disposition research and this implementation.

One direct check was still performed, since the charter requires it regardless:
a repository-wide search for `btctl`, `BATTLE_AGENTS_JSON`, `tournament/scripts`,
`tournament/roster`, and `sdk/tooling/build.sh` turned up a reference not
previously listed by Phase 2B.2 — `docs/specs/agent_designer_workflow.md:137-148`,
which describes `battle_engine.cli.py`'s `_load_agents_spec_from_env` as
consulting `BATTLE_AGENTS_DIR` for "the legacy `BATTLE_AGENTS_JSON` back-compat
path," and describes `AgentCatalog.agents_dir()` consulting the same name as a
"test-only override."

This was verified directly against source rather than accepted at face value:
`grep -n "BATTLE_AGENTS_JSON\|BYTEFRAY_AGENTS_JSON\|BATTLE_AGENTS_DIR\|BYTEFRAY_AGENTS_DIR" engine/src/battle_engine/cli.py`
returns only `BYTEFRAY_AGENTS_JSON`/`BYTEFRAY_AGENTS_DIR` (lines 246–260, 493);
zero hits for the `BATTLE_*` names. A repository-wide grep of `app/` for either
`BATTLE_AGENTS_DIR` or `BATTLE_AGENTS_JSON` returns zero hits. **The spec's
claim does not match current source on either count** — it describes a
mechanism (using the pre-rename `BATTLE_*` names) that does not exist anywhere
in the current tree, in either `cli.py` or `app/`. This is unrelated to
`tournament/`/`btctl.py` specifically — it concerns a separate, already-dead
`BATTLE_AGENTS_DIR` override path for the Designer's own agent catalog — and it
does not disturb Phase 2B.2's finding that the engine reads only
`BYTEFRAY_AGENTS_JSON`. Recorded as an unexpected finding (§L), not corrected
here (out of scope — it is a pre-existing spec-staleness issue, not a
tournament-harness reference).

No evidence was found that contradicts Phase 2B.2's REMOVE disposition.
Proceeded with removal.

---

## C. Removed subsystem

`tournament/` was a pre-1.0 developer harness (introduced in the original
repository migration, `dc3dfb1`, 2025-09-29) consisting of a standalone
Python match-controller (`btctl.py`, 6 subcommands: `build`/`smoke`/`sweep`/
`roundrobin`/`elim`/`report`) that reached the engine only via subprocess
(`python -m battle_engine run`) plus manual `PYTHONPATH` injection and an
undocumented environment-variable hook. It was never imported by any product
module, never registered as a console script, never packaged in the wheel or
sdist, and never referenced in any user-facing documentation except two
disclaimers stating it was *not* the supported path. Phase 2B.2 reproduced
four independent failures in it (missing `build.sh`, a dead `BATTLE_AGENTS_JSON`
environment hook, a Windows `UnicodeEncodeError` in its report writer, and no
explicit `--ruleset` selection).

**Deleted (9 tracked files, via `git rm`):**

```
tournament/roster.json
tournament/rosters/default.json
tournament/rosters/derived.csv
tournament/scripts/btctl.py
tournament/scripts/cla-vs-cgpt.sh
tournament/scripts/round_robin.sh
tournament/scripts/smoke.sh
tournament/scripts/test_hunter.sh
engine/tests/test_tournament_btctl.py
```

No compatibility stub, hollow directory, or commented-out remnant was left in
place. The tree is fully recoverable from git history (`2ac55bb` and every
prior commit) if ever needed.

---

## D. Current Tournament protection

The following current, shipped Tournament-feature components were identified
per Phase 2B.2 §H and deliberately left untouched:

- `engine/src/battle_engine/tournament_service.py` (`TournamentService`)
- `engine/src/battle_engine/tournament_cli.py` and its `command.py:41`
  dispatch (`bytefray tournament` CLI)
- `app/views/tournament.py`, `app/services/tournament_results.py` (Designer
  GUI: Tools → Run Tournament…, Tournament Results/History views)
- `engine/src/battle_engine/agent_evaluation.py` (Evaluation; adjacent, not
  part of the tournament subsystem, not affected)
- `client/src/battle_client/` replay/session code and
  `engine/src/battle_engine/replay_history/` (replay/history integration)
- The `tournament.json` artifact and `battle2.tournament` schema v1
- `engine/src/battle_engine/agent_package.py` (agent-package behavior)

None of these import, reference, or depend on anything under the removed
`tournament/` tree (one-way dependency was outward only: `btctl.py` consumed
the `bytefray run` CLI; nothing consumed `btctl.py`). This is confirmed
functionally in §H below, not merely asserted.

---

## E. Tests removed

`engine/tests/test_tournament_btctl.py` (7 tests) was removed with the
subsystem it exclusively tested. Per Phase 2B.2 §G, none of the seven exercised
real engine behavior:

| Test | Why it belonged only to the obsolete harness |
|---|---|
| `test_import_does_not_resolve_build_tool` | Asserts static import structure of `btctl.py` only |
| `test_report_does_not_load_roster_or_resolve_build_tool` | Mocks `aggregate_leaderboard` itself; tests argparse routing, not behavior |
| `test_default_battle_command_uses_current_source_dispatcher` | Tautological — asserts `_battle_cmd()` returns exactly what it is hard-coded to return |
| `test_run_game_uses_supported_arguments_and_current_environment` | Mocks `subprocess.run`; asserts the **dead** `BATTLE_AGENTS_JSON` name under a "current environment" label |
| `test_build_script_resolution_prefers_override_then_current_tool` | Structurally cannot observe that the real tree has no `build.sh`; tests only the resolution algorithm in isolation |
| `test_build_customs_uses_current_build_script_contract` | Asserts a command shape against `sdk/tooling/build.sh`, a path deleted in `6feb10b`, over a year before this phase |
| `test_roster_is_portable_regular_json_file` | Asserts `tournament/roster.json` is a regular file — meaningless once the file is gone |

None of the seven imports, calls, or otherwise touches `TournamentService`,
`tournament_cli.py`, `app/views/tournament.py`, or any other current-product
module — confirmed both by Phase 2B.2's source trace (§H there) and by this
phase's own re-check before deletion.

---

## F. References cleaned

Two live-documentation edits, both removals of disclaimer text that existed
solely to distinguish the product feature from the now-removed harness:

- `docs/TOURNAMENTS.md` (previously line 42): removed the trailing clause
  `"; it does not use \`tournament/scripts/btctl.py\`"` from the sentence
  describing the CLI's agent-discovery behavior.
- `docs/TOURNAMENTS.md` (previously lines 97–98): removed the sentence
  `"The older \`tournament/scripts/btctl.py\` remains a legacy standalone
  workflow and is not the supported execution path."` The preceding
  non-goals sentence (bracket visualization, parallel scheduler, etc.) was
  kept — it states product scope independently of the removed harness.

One configuration edit:

- `.gitignore` (previously line 24): removed the `agents_build/` entry —
  `btctl.py`'s default custom-agent build output directory. Re-verified before
  removal that nothing else references it (`grep -r agents_build` across the
  repository now returns only the historical Phase 2B.2 report and the
  `.gitignore` line itself, pre-edit).

No CI workflow, `pyproject.toml` entry, or packaging manifest required any
change — Phase 2B.2 verified, and this phase reconfirmed, zero references in
any of those files.

---

## G. Historical references retained

Left fully intact, as required:

- `docs/research/v6/V6_PHASE2B2_TOURNAMENT_DISPOSITION.md` and
  `V6_PHASE1_REPOSITORY_DIET_AUDIT.md` — the research records explaining why
  removal occurred.
- `docs/archive/v1/V1_4_PLATFORM_INTEGRITY.md`,
  `docs/archive/v4/V4_SPECTATOR_PHASE_4_RESEARCH.md`,
  `docs/archive/v5/V5_POST_RELEASE_H1_PARAMETER_CONSISTENCY.md`,
  `docs/archive/v5/V5_FINAL_REPLAY_NEWLINE_REMEDIATION.md`,
  `docs/archive/v5/V5_ALPHA1_MAINTENANCE_PHASE1_DOC_REPO_CLEANUP.md` —
  historical archive documents describing past events; none rewritten.
- `docs/RUFF_DEBT.md:46` — a historical bookkeeping note recording a past
  lint pass fixed 5 `C408` findings in `btctl.py`; left as-is per Phase
  2B.2's explicit instruction not to falsify a record of completed work.

---

## H. Targeted product verification

Run against the post-removal working tree, before the full canonical suite:

```
python -m pytest engine/tests/test_tournament_service.py engine/tests/test_tournament_results.py -q
→ 55 passed, 0 failed   (35 + 20, matching the pre-removal collected counts for these files exactly)

python -m pytest engine/tests/test_command.py engine/tests/test_launchers.py engine/tests/test_designer_workflows.py -q
→ 66 passed, 1 skipped, 0 failed
```

`test_designer_workflows.py` specifically exercises
`test_tournament_command_validates_runtime_and_uses_supported_cli` and
`test_tournament_state_is_adapted_to_status_and_standings` — the GUI-workflow
wiring from the Designer's Tournament launcher through to status/standings
presentation. All 122 targeted tests across these five files pass with zero
failures, confirming removal of the obsolete harness has no effect on the
real Tournament/Evaluation/replay-integration product surfaces.

---

## I. Canonical qualification

| Metric | Before | After |
|---|---:|---:|
| Collected tests | 3,741 | 3,734 |
| Test files | 160 | 159 |

**Reduction: exactly 7 tests, 1 file** — precisely `test_tournament_btctl.py`,
with no other change to collection. This matches Phase 2B.2's prediction
exactly (§L.2: "Canonical collected count moves 3,741 → 3,734").

Full suite (`python -m pytest -q`, clean working tree, `--basetemp` cleaned up
before linting per Phase 0's documented precondition):

```
3,712 passed, 22 skipped, 0 failed, 0 errors   (3,734 total, matching collection exactly)
```

The 22 skipped count matches Phase 0's baseline skip count exactly, consistent
with no skip-marker change anywhere in this phase's diff.

```
ruff check .        → All checks passed!
mypy engine/src/battle_engine   → Success: no issues found in 114 source files
mypy client/src/battle_client   → Success: no issues found in 16 source files
```

(Note: an initial `ruff check .` run while the full pytest run was still
executing in the background produced 27 spurious findings inside the
still-live `.pytest-tmp-2b3-full/` basetemp directory — exactly the false-positive
pattern Phase 0 §4 documented and warned against. The basetemp directory was
deleted and `ruff` re-run cleanly once the pytest run finished, producing the
clean result above. No source defect was ever present.)

---

## J. Packaging verification

```
python -m build --wheel  → bytefray-5.0.0-py3-none-any.whl, 215 entries, 0 starting with "tournament/", 0 containing "btctl"
python -m build --sdist  → bytefray-5.0.0.tar.gz, 283 entries, 0 containing "/tournament/", 0 containing "btctl"
```

Both entry counts (215, 283) are identical to Phase 2B.2's pre-removal
baseline — confirming, as expected, that this is a **source-tree reduction
only**. The harness was never included in either artifact, so its removal
changes neither package's contents nor size in any measurable way.

---

## K. Measured reduction

| Metric | Value |
|---|---:|
| Tracked files removed | 9 (8 under `tournament/` + 1 test file) |
| Python LOC removed | 533 (`btctl.py`: 372; `test_tournament_btctl.py`: 161) |
| Other LOC removed (shell + JSON/CSV) | 610 (591 shell across 4 `.sh` files; 19 JSON/CSV across `roster.json`/`rosters/default.json`/`rosters/derived.csv`) |
| Total LOC removed | 1,143 (`git diff --cached --stat` reports "9 files changed, 1143 deletions(-)") |
| Bytes removed | 43,481 (`tournament/` subtree: 38,365 bytes, matching Phase 2B.2's "~38 KB" estimate; `test_tournament_btctl.py`: 5,116 bytes) |
| Test files removed | 1 |
| Tests removed from collection | 7 |
| Directories eliminated | 3 (`tournament/`, `tournament/scripts/`, `tournament/rosters/`) |

### Repository reduction
Real: 9 files, 1,143 lines, 43,481 bytes, 3 directories, 7 tests removed from
the source tree.

### Distribution reduction
Zero, as expected and predicted by Phase 2B.2 (§14) — the harness was never
packaged in the wheel or sdist to begin with, so there is nothing to reduce
there.

---

## L. Unexpected findings

Recorded without opportunistic remediation, per the charter:

1. **A stale, pre-rename documentation claim unrelated to `tournament/`.**
   `docs/specs/agent_designer_workflow.md:137–148` describes
   `battle_engine.cli.py`'s `_load_agents_spec_from_env` as having a "legacy
   `BATTLE_AGENTS_JSON` back-compat path" via `BATTLE_AGENTS_DIR`, and
   describes `AgentCatalog.agents_dir()` (`app/services/agent_catalog.py:27`)
   as consulting the same name as a test-only override. Direct source checks
   in this phase found **zero** references to either `BATTLE_AGENTS_JSON` or
   `BATTLE_AGENTS_DIR` anywhere in `engine/src/battle_engine/cli.py` or
   anywhere under `app/` — only the renamed `BYTEFRAY_AGENTS_JSON`/
   `BYTEFRAY_AGENTS_DIR` exist in current source. This spec paragraph appears
   to predate the `BATTLE_*` → `BYTEFRAY_*` rename (the same rename Phase
   2B.2 §N.5 flagged as having silently orphaned `btctl.py`) and was never
   updated. It does not reference `tournament/` or `btctl.py` and describes a
   different, already-dead mechanism (the Designer's own catalog-scan
   override), so it is out of this phase's scope — flagged here for a future
   documentation-hygiene pass, not corrected.
2. **Orphaned bytecode cache.** `engine/tests/__pycache__/` retained four
   `test_tournament_btctl.cpython-3{10,11,12,13}-pytest-9.1.1.pyc` files
   referencing the now-deleted test module. These are gitignored and were
   never tracked (confirmed: `git ls-files | grep -i pycache` returns zero
   results, consistent with Phase 1's earlier finding that no `.pyc` file is
   tracked anywhere in this repository). Left untouched — they affect no git
   state and will be superseded on the next test run.

Neither finding contradicts Phase 2B.2's disposition or bears on the
correctness of this removal.

---

## M. Final repository state

```
git diff --check   → (clean, exit 0 — no whitespace errors)

git status:
  On branch v6-research
  Your branch is up to date with 'origin/v6-research'.
  Changes to be committed:
    deleted:    engine/tests/test_tournament_btctl.py
    deleted:    tournament/roster.json
    deleted:    tournament/rosters/default.json
    deleted:    tournament/rosters/derived.csv
    deleted:    tournament/scripts/btctl.py
    deleted:    tournament/scripts/cla-vs-cgpt.sh
    deleted:    tournament/scripts/round_robin.sh
    deleted:    tournament/scripts/smoke.sh
    deleted:    tournament/scripts/test_hunter.sh
  Changes not staged for commit:
    modified:   .gitignore
    modified:   docs/TOURNAMENTS.md

git rev-parse main origin/main
  82549f9c3ccbdb2e13b8165b32afef00def4a8f2
  82549f9c3ccbdb2e13b8165b32afef00def4a8f2
```

`main` is unchanged from every prior V6 phase's recorded value. Per the phase
charter (§18), **no commit was made** — this removal is left in the working
tree, staged and unstaged as shown above, for review.

---

## Success criteria — status

1. Obsolete pre-1.0 tournament harness completely removed — **done** (§C).
2. Tests validating only that harness removed with it — **done** (§E).
3. No hollow compatibility scaffolding remains — **confirmed** (§C; no stub,
   no commented-out source, no restored `sdk/`).
4. Current `TournamentService` and user-facing Tournament features remain
   untouched and green — **confirmed** (§D, §H).
5. Archived historical evidence remains intact — **confirmed** (§G).
6. No live dangling references remain — **confirmed** (§F, §L.1: the one
   remaining stray reference is unrelated to `tournament/`/`btctl.py`).
7. Canonical collection changes exactly as expected — **confirmed**, 3,741 →
   3,734 (§I).
8. Wheel/sdist still build normally — **confirmed** (§J).
9. `warriors/` remains completely independent and untouched — **confirmed**:
   this phase made zero references to, and zero changes under, `warriors/`.

---

## Appendix: reproduction commands

```bash
git rev-parse HEAD                                  # 5f7f1886495f52b732301d1955424c79a25a746e (phase start)
git status --porcelain                              # (clean, phase start)
git fetch --all --prune && git status -sb           # ## v6-research...origin/v6-research (no ahead/behind)
git rev-parse main origin/main                      # 82549f9c... twice, both before and after

python -m pytest --collect-only -q                  # 3,741 collected (before) -> 3,734 (after)

git rm -r tournament/
git rm engine/tests/test_tournament_btctl.py

python -m pytest engine/tests/test_tournament_service.py engine/tests/test_tournament_results.py -q
python -m pytest engine/tests/test_command.py engine/tests/test_launchers.py engine/tests/test_designer_workflows.py -q

python -m pytest -q                                 # 3,712 passed, 22 skipped, 0 failed, 0 errors
ruff check .                                         # All checks passed!
mypy engine/src/battle_engine                        # Success: no issues found in 114 source files
mypy client/src/battle_client                        # Success: no issues found in 16 source files

python -m build --wheel --outdir <scratch>
python -m build --sdist --outdir <scratch>
python -c "import zipfile; print(len(zipfile.ZipFile('<whl>').namelist()))"       # 215
python -c "import tarfile; print(len(tarfile.open('<tgz>').getnames()))"          # 283

git diff --check                                     # (clean)
git status                                            # 9 deletions + 2 modified docs, unstaged/staged, uncommitted
```
