# Bytefray V6 — Phase 2B.6: Redcode/pMARS Retirement (Implementation)

**Phase type:** Implementation/removal. Executes the retirement manifest
established by `V6_PHASE2B5_REDCODE_PMARS_RETIREMENT_AUDIT.md`. No commit or
push was performed — the complete verified retirement is left in the working
tree for review, per this phase's own instructions.

**Governing product decision:**

> Bytefray V6 retires Redcode and pMARS completely. V6 supports the Bytefray
> programmable-agent runtime only.

**Open decision resolved:** `bytefray run --mode` is removed entirely. No
`--mode native` compatibility flag was preserved.

---

## A. Baseline

| Item | Value |
| --- | --- |
| Branch | `v6-research` — confirmed |
| HEAD SHA at phase start (and throughout — no commit made) | `9c480ee25e8dc635cc86008b73a6073388129576` ("V6 Phase 2B5 redcode pmars retirement") |
| Working tree at start | Clean (`git status --porcelain` empty) |
| Divergence from `origin/v6-research` | 0 ahead, 0 behind (`git rev-list --left-right --count`) |
| `main` | `82549f9c3ccbdb2e13b8165b32afef00def4a8f2`, identical to `origin/main` — untouched throughout |
| Canonical test count before removal | **3,734 collected across 158 files** — reconfirmed independently by summing `pytest --collect-only -q`'s per-file counts; matches the audit's recorded baseline exactly |

Phase 2B.5 was already committed at session start (it is HEAD), so no
synchronization step was required. Re-inspection of `cli.py`, `pmars.py`, and
the full repository-wide `pmars`/`redcode` grep confirmed **no commits since
the audit changed the dependency surface** — every line number, file list,
and classification in the audit matched current source exactly before any
edit was made.

---

## B. Product decision implemented

Bytefray V6 now executes **Bytefray programmable agents only**. `bytefray run`
has a single, implicit execution model (native VM/Python via
`NativeMatchService`). There is no `--mode` selector, no `redcode94` branch,
and no pMARS integration anywhere in the production tree. Historical Redcode
result records remain readable (see §I). Releases up to and including
v5.0.0 retain full Redcode/pMARS support and remain available via Git
history and prior release artifacts.

---

## C. Production removal

- **Full file removed:** `engine/src/battle_engine/pmars.py` (255 lines,
  8,839 bytes) — the sole pMARS integration module. Confirmed it has no
  other importer anywhere in the repository before deletion.
- **`engine/src/battle_engine/cli.py`** — removed, verbatim, with no
  opportunistic tidying beyond dead-import cleanup exposed by the removal
  itself:
  - `from battle_engine.pmars import PMarsError, run_pmars`
  - `from battle_engine.result_model import SCHEMA_VERSION_V1 as RESULT_SCHEMA_VERSION_V1`
  - `_pmars_arguments()` (29 lines)
  - the `# ICWS'94 / pMARS backend flags` block — `--mode`, `--red-a`,
    `--red-b`, `--core-size`, `--max-cycles`, `--max-processes`,
    `--max-len`, `--min-dist`, `--rounds` (26 lines)
  - `if args.mode == "redcode94": … return 0` (104 lines)
  - Additionally removed, because the redcode94 branch was their only
    remaining call site in this module: the `hashlib` import and the
    `stable_id`, `write_json_atomic`, `ResultEnvelope` names from the
    `result_model` import (these symbols still have live callers elsewhere
    in the repository; they were never used by `cli.py`'s *native* path).
  - Net: `cli.py` went from **1,062 → 894 lines** (−168).
- **`engine/src/battle_engine/command.py`** — subcommand help text changed
  from `"run a native Bytefray or pMARS match"` to `"run a native Bytefray
  match"`.
- **Preserved exactly as instructed:** `_resolve_replay_path`,
  `_resolve_trace_path`, `stable_id`, `write_json_atomic`, `ResultEnvelope`
  (all still imported/used by native code paths elsewhere), and all native
  execution logic in `main()`. No native-path refactor was performed beyond
  the direct dead-branch/dead-import removal.

---

## D. CLI changes

### Retired-option inventory (9 options removed from `bytefray run`)

| Option | Disposition |
| --- | --- |
| `--mode` | **Removed entirely** (no `native`-only compatibility flag preserved, per the resolved open decision) |
| `--red-a` | Removed |
| `--red-b` | Removed |
| `--core-size` | Removed |
| `--max-cycles` | Removed |
| `--max-processes` | Removed |
| `--max-len` | Removed |
| `--min-dist` | Removed |
| `--rounds` (the `bytefray run` copy) | Removed |

Verified by running `bytefray run --help` (via `python -m battle_engine.cli
--help`): none of the nine options appear.

### Critical trap avoided

`tournament_cli.py`'s independent `--rounds` was traced by parser/command
ownership (not global flag-name search) and left completely untouched.
Verified behaviorally: `bytefray tournament --help` still shows `--rounds`,
and a live tournament run (`bytefray tournament --rounds 2 --ticks 100
--arena 128 --seed 7 runner writer seeker`) completed and produced a valid
`tournament.json`.

### Decisive negative proof

```
$ python -m battle_engine.cli --mode redcode94 --red-a x --red-b y
usage: bytefray run [-h] [--ticks TICKS] ...
bytefray run: error: unrecognized arguments: --mode redcode94 --red-a x --red-b y
(exit code 2)
```

No current surface claims or attempts Redcode execution.

---

## E. Warriors/pMARS removal

| Path | Bytes | Disposition |
| --- | ---: | --- |
| `warriors/aeka.red` | 4,018 | Removed |
| `warriors/validate.red` | 2,821 | Removed |
| `warriors/pspace.red` | 1,510 | Removed |
| `warriors/flashpaper.red` | 1,095 | Removed |
| `warriors/rave.red` | 784 | Removed |
| `warriors/test_eval.red` | 473 | Removed |
| `warriors/dwarf.red` | 110 | Removed |
| `warriors/imp.red` | 72 | Removed |
| `pmars/windows/pmars.exe` | 150,528 | Removed (bundled GPL binary) |
| `pmars/windows/COPYING` | 17,997 | Removed (pMARS GPL-2.0-or-later text) |
| `third_party_licenses/pmars-GPL-2.0-or-later.txt` | 17,997 | Removed (byte-identical duplicate) |

`warriors/`, `pmars/`, and `third_party_licenses/` are now gone entirely
(all three directories are empty after these removals and were deleted with
`git rm -r`). Nothing was archived elsewhere in the active repository —
Git history and prior releases preserve all of it. Bytefray's own `LICENSE`
was not touched.

---

## F. Packaging/installer changes

- **`tools/bytefray.spec`** — removed `pmars_dir = …`, the 11-line pMARS
  rationale comment, and the `if sys.platform == "win32" and
  os.path.isdir(pmars_dir):` bundling block (19 lines total).
- **`tools/bytefray_cli.spec`** — removed `pmars_dir = …` and its bundling
  block; reworded the cross-reference comment to drop the now-stale
  pMARS-bundling pointer while keeping the starter_agents cross-reference.
- **`tools/check_wheel.py`** — `ALLOWED_PMARS_PATHS` changed from
  `{"battle_engine/pmars.py"}` to `frozenset()`, with a comment explaining
  the guard is now a permanent anti-regression check (§25's Phase 3 finding
  #10 acted on directly, since it required no design decision). The
  wheel-content assertion logic itself (`:94-103` in the audit's numbering)
  was **not** touched, per the audit's explicit instruction to keep it
  permanently.
- **`pyproject.toml`** — removed `"pmars"` from `keywords` (kept
  `"corewar"` as project lineage, per the audit's U.3.2 recommendation);
  reworded the package-data rationale comment; deleted the commented-out
  `[tool.setuptools.data-files]` example naming `warriors/*` and
  `third_party_licenses/*` (§18 — removed rather than left as a latent
  trap).
- **Not touched, confirmed no edits needed:** `tools/agent_designer.spec`,
  `tools/replay_viewer.spec`, `MANIFEST.in`, `tools/installer.iss`,
  `tools/build_win.ps1` — none reference pMARS.

---

## G. CI changes

- **Deleted:** `.github/workflows/linux-pmars-build.yml` (250 lines,
  9,215 bytes) — built upstream pMARS, validated upstream `validate.red`,
  retained no artifact, and fed no release.
- **Searched all three surviving workflows** (`ci.yml`,
  `linux-gui-smoke.yml`, `linux-package.yml`) for pMARS-specific steps:
  none found. `ci.yml`'s indirect reference (invoking `check_wheel.py`) is
  a negative assertion tool, already updated in §F; no workflow YAML edit
  was needed.
- **Verified no dangling references** to the deleted workflow: no other
  tracked file (documentation links, status-check requirements, workflow
  `needs:`/`uses:` dependencies) mentions
  `linux-pmars-build.yml` or its display name ("Ubuntu 22.04 pMARS build
  validation") outside historical/archived/research documents.

---

## H. Test changes

### Removed

- **`engine/tests/test_pmars.py`** — full file, 308 lines, 12,302 bytes,
  21 test cases (executable discovery, subprocess construction,
  execution/error normalization, CLI mode behavior, GUI-subprocess
  failure).
- **`engine/tests/test_cli_characterization.py::test_engine_cli_starts_and_displays_help`**
  — the single assertion `assert "--mode {native,redcode94}" in
  result.stdout` was replaced with nine assertions proving the retired
  options are **absent** from `--help` output (`--mode`, `redcode94`,
  `--red-a`, `--red-b`, `--core-size`, `--max-cycles`, `--max-processes`,
  `--max-len`, `--min-dist`, `--rounds`), plus one positive assertion
  (`--quota`) so the test cannot pass vacuously.

### Preserved (historical-compatibility coverage — critical)

All four Redcode cases in `engine/tests/test_ruleset_persistence.py` were
**kept unchanged in behavior** (docstrings left as-is; they already read as
compatibility tests, not feature tests):

- `test_resolve_result_ruleset_not_applicable_for_redcode`
- `test_resolve_result_ruleset_never_stamps_redcode_even_if_field_were_present`
- `test_redcode_result_as_dict_carries_ruleset_id_key_with_null_value`
- `test_redcode_result_missing_ruleset_id_key_entirely_still_resolves_not_applicable`

All four pass (verified in isolation: `4 passed, 16 deselected`). The
corresponding reader logic in `result_model.py` (`resolve_result_ruleset`'s
`if envelope.mode == "redcode94": return RulesetProvenance(None,
"not_applicable")`) was **not** altered — only its surrounding comment was
reworded to past tense.

### Also confirmed unchanged (generic fixtures, not Redcode-specific)

`test_cli_agent_listing.py` (docstring reworded only, assertions
unchanged), `test_replay_history.py` (both `redcode94`-fixture cases kept
verbatim), `test_designer_workflows.py`, `test_install_docs_consistency.py`,
`test_windows_packaging_spec.py`, `test_check_wheel.py`,
`tests/test_v5_replay_history_qualification.py` (outside canonical
`testpaths`, unaffected either way).

---

## I. Historical-readability qualification

A standalone script (run from the session scratchpad, not committed)
reproduced Phase 2B.5's §N.2 behavioral proof **after** `pmars.py` no
longer exists at all, rather than merely being unimported:

```
READ OK       : redcode94 1 winner= A
RULESET PROV  : RulesetProvenance(value=None, confidence='not_applicable')
HISTORY ROW   : replay_state= ReplayState.NOT_PRODUCED ruleset_conf= not_applicable
DETAIL        : True
RESOLVE REPLAY: ReplayResolution(state=<ReplayState.NOT_PRODUCED>, path=None, ...)
GUI LABEL     : ruleset= N/A
GUI STATE     : replay_state_label= Not produced
battle_engine.pmars in sys.modules? -> False
battle_engine.pmars importable? -> False (ModuleNotFoundError, as expected)

ALL HISTORICAL-READABILITY ASSERTIONS PASSED
```

A historical `redcode94` `result.json` (schema v1, `replay: null`,
`backend: {"name": "pMARS"}` — exactly the shape the retired writer used)
was placed under an isolated data root and read through
`read_result`/`resolve_result_ruleset`, indexed by
`ReplayHistoryService`, fetched via `fetch_detail`, resolved via
`resolve_replay`, and rendered through
`app.services.replay_history_presentation.ruleset_label`/
`REPLAY_STATE_LABELS` — the full stack from persisted artifact to GUI
label, with `battle_engine.pmars` confirmed both absent from
`sys.modules` and genuinely non-importable (`ModuleNotFoundError`, not
merely unimported).

---

## J. Documentation changes

### Current documentation rewritten (18 files touched)

Live docs edited to remove active Redcode/pMARS support claims, reframed to
past tense where describing retired behavior: `README.md`, `INSTALL.md`,
`SECURITY.md`, `AGENTS.md`, `ARCHITECTURE.md`, `docs/AGENT_AUTHORING.md`,
`docs/LINUX_INSTALL.md` (entire Linux-pMARS paragraph and worked example
removed), `docs/MANUAL_SMOKE_TESTS.md` (entire "pMARS / Redcode
integration" procedure removed), `docs/COMPATIBILITY.md`,
`docs/RULES.md` (retitled "Redcode/pMARS — not Ruleset v1 (historical)"
and reworded as an explicit historical section — all four internal
cross-references updated to match), `docs/FUTURE_PLANS.md` (turned into an
explicit retirement statement instead of "not cancelled"),
`docs/RESULT_SCHEMA.md`, `docs/TOURNAMENTS.md`, plus three
`docs/specs/*.md` files whose design-precedent citations of `pmars.py`
would otherwise point at a deleted file (`agent_lab.md` — three sites
reworded to name the Designer's `QProcess` pattern as the *current*
precedent and `pmars.py` as historical; `agent_evaluation.md`;
`agent_validation.md:578`, whose table row was reworded from a present-tense
`--mode redcode94` example to an explicit historical framing). Finally,
`docs/specs/run_match_pmars.md` was deleted outright — it documented a
`backends/pmars.py` module and `run_match_pmars()` function that never
existed in the codebase (a stale spec Phase 1 had already flagged for
reconciliation; retirement closes it by deletion).

`app/services/ruleset_options.py`'s two identified comment lines were
reworded to reflect the retirement while keeping their factual content
(Redcode/pMARS uses no Bytefray Ruleset).

`CHANGELOG.md` gained a new `## [Unreleased]` section (none existed before
this phase) with a "Removed — Redcode/pMARS support" entry per §S.3's
suggested wording, naming every retired flag and confirming historical
readability. No prior release entry was edited.

### Historical documentation deliberately left untouched

`docs/archive/**`, `docs/releases/**`, `docs/research/**` (other than this
new report), all prior `CHANGELOG.md` entries, `docs/ROADMAP.md` (including
its v0.10 "Redcode/pMARS interoperability remains part of Bytefray's story"
item — left as an accurate historical record, now superseded by the new
`CHANGELOG.md`/`FUTURE_PLANS.md` entries rather than edited in place, per
the audit's U.3.5 recommendation), `README.md`'s "Bytefray vs. Core War"
table (already correctly asserted no Redcode implementation claim),
`pyproject.toml`'s `"corewar"` keyword and "inspired by Core War"
description, `docs/PROJECT_HISTORY.md`, and all `docs/specs/agent_*.md`
scope-exclusion lines that already read as true after retirement
(`agent_designer_workflow.md`, `agent_package.md`, `agent_scaffold.md`,
`agent_test.md`) — none of these were edited, matching the audit's K.3
classification exactly.

---

## K. Targeted native-runtime qualification

All run from a live shell against the modified source tree (`PYTHONPATH`
pointed at `engine/src`, `client/src`, repo root):

1. **`bytefray --help`** shows `run` described as `"run a native Bytefray
   match"` (no "or pMARS").
2. **`bytefray run --help`** shows none of the nine retired options; shows
   `--quota`, `--ticks`, `--arena`, `--ruleset`, and all native flags
   unchanged.
3. **Native match execution**: `python -m battle_engine.cli --ticks 200
   --arena 128 --seed 42 --a-type runner --b-type writer --quiet` produced
   `replay.jsonl`, `result.json`, and `summary.json` under an isolated
   `BYTEFRAY_ROOT`, with a fully populated `battle2.result` envelope.
4. **Tournament (independent `--rounds`)**: `bytefray tournament --rounds 2
   --ticks 100 --arena 128 --seed 7 --output <dir> runner writer seeker`
   completed and produced a valid `tournament.json`.
5. **`battle_engine.pmars` does not exist**: `import battle_engine.pmars`
   raises `ModuleNotFoundError`.
6. **Decisive negative CLI proof** (§D): `--mode redcode94 ...` fails as
   an unrecognized argument, exit code 2, before any execution is
   attempted.

---

## L. Packaging qualification

### Wheel and sdist

Built with `python -m build`; both succeeded.

- **Wheel** (`bytefray-5.0.0-py3-none-any.whl`): `tools/check_wheel.py`
  passes with `ALLOWED_PMARS_PATHS` empty; a direct archive-member search
  for `pmars`/`warrior`/`.red` (case-insensitive) returns nothing.
- **sdist** (`bytefray-5.0.0.tar.gz`): same archive-member search returns
  nothing — no `pmars`, no `warriors/`, no Redcode runtime module.

### Windows frozen build

Ran `tools/build_win.ps1` end-to-end (installs `.[replay,designer,windows-build]`
extras, builds all four PyInstaller onedir trees, runs the built-in GUI
startup smoke with `BYTEFRAY_GUI_SMOKE_EXIT_MS=750`, and the "agents
create" smoke suite). **Exit code 0; all four artifacts built; both smoke
suites passed.**

- `find dist/windows -iname "*pmars*"` — **empty** across all four trees
  (`bytefray`, `bytefray-cli`, `bytefray-agent-designer`,
  `bytefray-replay-viewer`).
- Confirmed no PyInstaller "missing resource" error — the specs no longer
  reference `pmars_dir` at all, so nothing was looked for and nothing was
  missing.

### Windows installer

Built with the repository's own Inno Setup 6 toolchain
(`%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe tools\installer.iss`) —
**successful compile**, producing `dist/installer/Bytefray-Setup-5.0.0.exe`
(~101 MB). A best-effort string search of the compiled installer for
`pmars.exe`/`pmars/windows` found nothing; combined with the confirmed-clean
source `dist/windows` trees the installer packages verbatim
(`recursesubdirs`), this is conclusive.

### Qualification tier reached, and the tier explicitly not reached

Per this repository's qualification-tier honesty standard: the above is
**source qualification** and **packaged qualification**. **Interactive
first-user (installed-application) qualification was not performed** —
this machine's coding-agent session is non-interactive and non-elevated,
and the installer requires admin privileges
(`PrivilegesRequired=admin` in `tools/installer.iss`). This machine also
already has a real Bytefray installation at the default paths
(`%ProgramFiles%\Bytefray`, `%ProgramData%\Bytefray`), so the handoff must
target an isolated pair, not the defaults (upgrading/uninstalling the
real install would be a destructive side effect of a qualification run).
The exact command to run in an elevated shell:

```powershell
pwsh tools\smoke_after_install.ps1 -AppDir "D:\Bytefray Test\Application" `
  -DataRoot "D:\Bytefray Test\Data" -Lifecycle
```

This uses the repository's own established tooling (not a hand-rolled
script) and installs to an isolated location. **This tier remains an open
item, not a skipped or faked one.**

---

## M. Canonical qualification

### Full suite

Ran sequentially (never overlapping), each invocation with its own
`--basetemp` under the repo-local `.pytest-tmp/`, per this repository's
qualification integrity protocol.

| Metric | Value |
| --- | --- |
| Collected | **3,713** |
| Passed | 3,693 |
| Skipped | 20 |
| Deselected (GUI-marked, excluded by `-m "not gui"`) | 3 |
| Failed | **0** |
| Errors | **0** |

**3,713-test tripwire: MET.** This is not 3,709 — the four historical
`test_ruleset_persistence.py` cases were correctly preserved (§H).

A first full-suite attempt (before this run) surfaced a single failure,
`test_agent_evaluation_multi_entrant.py::test_same_group_roster_with_changed_opponent_source_does_not_strict_align`,
with `PermissionError: [WinError 5] Access is denied` on an `os.replace`
rename of a temp file. Reproduced alone immediately afterward: **passed**.
This is a transient Windows file-lock/antivirus-scan flake unrelated to
this phase's changes (the test touches `agent_evaluation.py`/
`result_model.py`'s atomic-write path, not anything Redcode/pMARS-related),
confirmed by isolation before being dismissed, per the repository's
qualification protocol ("reproduce it alone first"). The clean re-run
reported above is fully green with zero failures.

### Lint and types

| Check | Command | Result |
| --- | --- | --- |
| Lint | `ruff check .` | **All checks passed** |
| Types (engine) | `mypy engine/src/battle_engine` | **Success: no issues found in 113 source files** (114 → 113, `pmars.py` removed) |
| Types (client) | `mypy client/src/battle_client` | **Success: no issues found in 16 source files** |

---

## N. Residue search

Ran `git grep -ni -E "pmars|redcode"` across the entire repository
excluding `docs/archive/`, `docs/research/`, `docs/releases/`, and
`CHANGELOG.md`, both before any edit (466 lines, all matching the audit's
predicted inventory exactly) and after all edits (127 lines remaining).
Every remaining hit was individually inspected and falls into one of the
three permitted categories:

### Historical

Prose explicitly framed as retired/historical (e.g. `README.md`'s artifact
formats row, `RULES.md`'s "(historical)" section, `FUTURE_PLANS.md`'s
retirement entry, `docs/ROADMAP.md`'s untouched v0.10 closed item).

### Historical-readability implementation

The minimal code required to understand old persisted result records:
`result_model.py`'s `mode == "redcode94"` branch and its reworded comments,
`rules.py`'s `not_applicable` literal and docstring, `replay.py`'s
`ruleset_id` docstring, `replay_history/models.py`'s `NOT_PRODUCED`
docstring, `replay_history/discovery.py`'s comment, `tournament_service.py`'s
comment, the four preserved `test_ruleset_persistence.py` cases and their
docstrings, the generic `redcode94`-fixture cases in `test_replay_history.py`
and `test_designer_workflows.py`, and `tools/check_wheel.py`'s permanent
negative-assertion guard.

### Project lineage / negative assertions

`pyproject.toml`'s `"corewar"` keyword, `README.md`'s "Bytefray vs. Core
War" comparison table, `data/starter_agents/hunter/agent.py`'s
design-rationale prose ("classic Redcode-bomber idea"),
`data/benchmarks/v3_phase2_locality_corpus.json`'s frozen research corpus,
`test_cli_agent_listing.py`'s negative assertion (`assert "pMARS" not in
out` — a test that becomes *more* true after retirement),
`test_install_docs_consistency.py`'s explanatory comment, and the
`docs/specs/agent_*.md` scope-exclusion lines left unedited because they
already read as true.

**No unacceptable hit was found**: no executable Redcode support, no
current CLI option, no bundled pMARS, no packaging hook, no current support
documentation, and no dormant configuration anywhere in the searched tree.
The negative-search checks the audit specified (`PMARS_CMD` outside
archives, `--mode redcode94` outside archives, tracked `.red` files, and
the four retired directories) all now return **empty**.

---

## O. Quantified reduction

All figures below are **measured directly** from `git diff`/`git cat-file`
against HEAD after the edits, not carried over from the audit's estimates.

| Dimension | Audit estimate | Actual measured |
| --- | ---: | ---: |
| Full files removed | 17 | **17** (exact match) |
| Production files removed | 1 | **1** (`pmars.py`) |
| Test files removed | 1 | **1** (`test_pmars.py`) |
| Test cases removed | 21 | **21** |
| Canonical tests removed | 21 (3,734 → 3,713) | **21** (3,734 → 3,713, confirmed both before and after) |
| `.red` files removed | 8 | **8** |
| CI workflows removed | 1 | **1** |
| Production LOC removed (full file + `cli.py` net) | ~442 | **423** (255 `pmars.py` + 168 net `cli.py`) |
| `cli.py` lines edited | ~161 | **168** (161 from the four audited blocks/imports, +7 from additional dead-import cleanup — `hashlib`, `stable_id`, `write_json_atomic`, `ResultEnvelope` — exposed once the branch was gone; verified each had no surviving native use in this module before removal) |
| Full-file lines removed (text files) | 1,395 | **2,075** (audit excluded the two GPL license files' 339 lines each — 678 total — from its "lines" tally as non-source text; **1,397** if those are likewise excluded, matching the audit almost exactly, with the residual 2-line difference from warriors' end-of-file whitespace) |
| Total tracked bytes removed (full-file) | 235,610 | **235,610** (exact match, verified via `git cat-file -s` on every deleted blob) |
| Partial-edit lines (36 modified files) | ~465 | **743** (527 removed + 216 added) — larger than estimated because documentation rewording (past-tense reframing, not pure deletion) accounts for most of the 216 insertions, and because `cli.py`'s dead-import cleanup added lines beyond the audit's four blocks |
| Windows release payload removed per tree | 337,050 (2 trees × 168,525) | **337,050** (confirmed behaviorally: both `bytefray` and `bytefray-cli` frozen trees built clean of all `pmars` material; `bytefray-agent-designer`/`bytefray-replay-viewer` never bundled it) |
| Documentation files edited | ~19 live | **17 live edited + 1 spec removed = 18 total** (fewer than estimated: `docs/REPLAY_SCHEMA.md` and `docs/ROADMAP.md` needed no edit on inspection — already correctly historical/reader-framed) |
| Packaging/configuration entries removed | 6 spec blocks + 3 `pyproject.toml` edits | **Matches**: `bytefray.spec` (3 blocks), `bytefray_cli.spec` (2–3 blocks), `check_wheel.py` (1 constant), `pyproject.toml` (keyword + 2 comment/block edits) |
| Total files changed | — | **53** (`git diff --stat`: 17 deleted + 36 modified) |
| Total lines changed | — | **216 insertions(+), 2,602 deletions(-)** |

---

## P. Phase 3 findings

Recorded for the later architecture/context-locality audit, per §26 —
**none of these were acted on beyond what direct dead-branch/dead-import
removal required.**

1. **`--mode`'s two-valued abstraction is now fully gone**, not merely
   reduced to one value — this phase implemented the audit's own
   recommendation (§U.1) in full. No further Phase 3 action needed on this
   specific item.
2. **`ResultEnvelope.backend` is now a write-dead schema field with zero
   writers anywhere in the repository.** It is retained solely for
   historical decode. Phase 3 should decide whether to document it as
   historical-only or keep it as a genuine extension point.
3. **`SCHEMA_VERSION_V1` has stopped being a write target.** Confirmed:
   `git grep -n "SCHEMA_VERSION_V1"` in production code now shows only the
   dataclass default and read-path handling, no writer. Phase 3 may want to
   revisit `result_model.py`'s `as_dict()` v1/v2 branch now that it is
   "one writer, one legacy read format."
4. **`termination_reason == "backend_completed"` has no writer.** Confirmed
   dead as a write value; reader tolerance intentionally retained.
5. **`RulesetConfidence`'s `"not_applicable"` is now purely historical** —
   every new artifact is `recorded`. The vocabulary now describes an
   artifact's era rather than a live distinction.
6. **`ReplayState.NOT_PRODUCED` has lost its only current producer** — its
   docstring was updated in this phase to say so explicitly. Reachable only
   by historical rows going forward.
7. **`cli.py` shrank from 1,062 to 894 lines** (−168, −16%). Its natural
   seam (the mode branch) is gone, which Phase 3 may find makes further
   extraction of `main()`'s parse/configure/dispatch responsibilities
   easier to reason about — but no such extraction was attempted here.
8. **Core War-era naming is untouched and unaffected**, as instructed:
   `SCHEMA_NAME = "battle2.result"`, `battle2.replay`, `battle_engine`/
   `battle_client` package names, `arena`/`core` vocabulary all remain
   exactly as they were. Phase 3's naming review should still treat these
   as one deliberate cluster, separately from this retirement.
9. **The smoke harnesses' triple fixture duplication is now single.**
   `warriors/`, `smoke_test.sh`'s heredoc warriors, and
   `smoke_after_install.ps1`'s inline warrior writes were three
   independent reinventions of the same fixture; two vanished with this
   retirement (the heredocs and the inline writes were deleted along with
   their Redcode test blocks). No remaining Redcode-related duplication to
   resolve.
10. **`tools/check_wheel.py`'s pMARS guard is now empty and permanent.**
    This phase already added a comment documenting it as a permanent
    anti-regression check rather than residue, partially pre-empting this
    Phase 3 recommendation — Phase 3 need not revisit this specific point.

---

## Q. Unexpected findings

Recorded without remediation, per §29's scope boundaries.

1. **`.pytest-tmp/` (the repo-local pytest basetemp parent) did not exist
   at session start.** `pytest --collect-only -q --basetemp=.pytest-tmp/x`
   succeeds even when `.pytest-tmp/` itself is absent (collection never
   creates the basetemp directory), but a real test-executing run fails
   every single test with `FileNotFoundError: [WinError 3]` from
   `Path.mkdir(parents=False)` when the parent doesn't exist. This produced
   a spurious "2,320 errors" result on the first full-suite attempt,
   entirely unrelated to source changes — recreating `.pytest-tmp/`
   resolved it immediately. This is a pre-existing environment/tooling
   quirk (not caused by this phase's changes) worth a `mkdir -p
   .pytest-tmp` guard somewhere in the test-running documentation or a
   `conftest.py` hook, but that is out of this phase's scope.
2. **One transient Windows `PermissionError` flake** in
   `test_agent_evaluation_multi_entrant.py::test_same_group_roster_with_changed_opponent_source_does_not_strict_align`
   during the first full-suite run (see §M). Confirmed non-reproducing in
   isolation and confirmed absent in the final clean full-suite run. Not a
   Redcode/pMARS-related regression; not remediated, per this phase's
   scope.
3. **A real Bytefray installation already exists on this machine** at the
   default installer paths (`%ProgramFiles%\Bytefray`,
   `%ProgramData%\Bytefray`). This blocks running the installed-application
   qualification tier against the default paths without risking the user's
   real installation/data; see §L for the isolated-path handoff command
   prepared instead.

---

## R. Final repository state

```
$ git diff --check HEAD -- .
warning: in the working copy of 'engine/tests/test_cli_agent_listing.py',
CRLF will be replaced by LF the next time Git touches it
```

No actual whitespace-error annotation was produced (no "trailing
whitespace" / "new blank line at EOF" lines) — the only output is Git's
routine `core.autocrlf` normalization notice for a file that was already
CRLF-terminated before this phase touched it (confirmed via `file`: the
entire file is uniformly CRLF both before and after the edit).

```
$ git status --short
D  .github/workflows/linux-pmars-build.yml
 M AGENTS.md
 M ARCHITECTURE.md
 M CHANGELOG.md
 M INSTALL.md
 M README.md
 M SECURITY.md
 M app/services/ruleset_options.py
 M docs/AGENT_AUTHORING.md
 M docs/COMPATIBILITY.md
 M docs/FUTURE_PLANS.md
 M docs/LINUX_INSTALL.md
 M docs/MANUAL_SMOKE_TESTS.md
 M docs/RESULT_SCHEMA.md
 M docs/RULES.md
 M docs/TOURNAMENTS.md
 M docs/specs/agent_evaluation.md
 M docs/specs/agent_lab.md
 M docs/specs/agent_validation.md
D  docs/specs/run_match_pmars.md
 M engine/src/battle_engine/cli.py
 M engine/src/battle_engine/command.py
 M engine/src/battle_engine/match_service.py
D  engine/src/battle_engine/pmars.py
 M engine/src/battle_engine/replay.py
 M engine/src/battle_engine/replay_history/discovery.py
 M engine/src/battle_engine/replay_history/models.py
 M engine/src/battle_engine/result_model.py
 M engine/src/battle_engine/rules.py
 M engine/src/battle_engine/ruleset_policy.py
 M engine/src/battle_engine/tournament_service.py
 M engine/tests/test_cli_agent_listing.py
 M engine/tests/test_cli_characterization.py
D  engine/tests/test_pmars.py
D  pmars/windows/COPYING
D  pmars/windows/pmars.exe
 M pyproject.toml
D  third_party_licenses/pmars-GPL-2.0-or-later.txt
D  tools/build_pmars_linux.sh
 M tools/bytefray.spec
 M tools/bytefray_cli.spec
 M tools/check_wheel.py
D  tools/pmars/README.md
 M tools/smoke_after_install.ps1
 M tools/smoke_test.sh
D  warriors/aeka.red
D  warriors/dwarf.red
D  warriors/flashpaper.red
D  warriors/imp.red
D  warriors/pspace.red
D  warriors/rave.red
D  warriors/test_eval.red
D  warriors/validate.red
?? docs/research/v6/V6_PHASE2B6_REDCODE_PMARS_RETIREMENT.md
```

`main`: `82549f9c3ccbdb2e13b8165b32afef00def4a8f2` — unchanged, still
identical to `origin/main`. `HEAD`: `9c480ee25e8dc635cc86008b73a6073388129576`
— unchanged throughout the entire phase; nothing was committed. Nothing was
stashed or discarded. `dist/`, `build/`, and `.pytest-tmp/` build/test
byproducts from this phase's qualification runs are git-ignored and do not
appear above.

Per §29, this report intentionally leaves everything uncommitted for
review.
