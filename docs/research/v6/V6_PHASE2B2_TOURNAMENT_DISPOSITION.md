# Bytefray V6 Research — Phase 2B.2: Tournament Pipeline Disposition

**Status:** Phase 2B.2 — research and disposition only. No tournament code was
repaired, deleted, refactored, or redesigned in this phase. No test, CI
workflow, packaging file, or documentation outside this report was modified.
Working tree left uncommitted for review per the phase charter (§16).

---

## A. Executive conclusion

`tournament/` is **not a broken version of Bytefray's Tournament feature.** It is
a pre-1.0 developer harness carried in from the original repository migration
(`dc3dfb1`, 2025-09-29) that has never been packaged, never been shipped, never
been reachable from any GUI or CLI, and never been advertised to users. The
product's actual tournament functionality — `bytefray tournament`,
`TournamentService`, and the Designer's Tournament Results/History views — was
built later, independently, and shares **zero code, zero artifacts, and zero
imports** with it. The two systems collide only on the word "tournament."

The breakage is materially worse than Phase 1 reported. Phase 1 identified one
failure (the missing `build.sh` following `sdk/` removal). This phase reproduced
**four independent failures**, of which the `sdk/` removal is only the first
visible one:

| # | Failure | Kind | Scope |
|---|---|---|---|
| 1 | `_find_build_sh()` → `FileNotFoundError` | Hard, deterministic | 5 of 6 subcommands, every platform |
| 2 | Sets `BATTLE_AGENTS_JSON`; engine reads `BYTEFRAY_AGENTS_JSON` | **Silent, result-corrupting** | Every custom-agent match, latent behind #1 |
| 3 | `UnicodeEncodeError` writing the `Δ` leaderboard header | Hard, platform-conditional | The 6th subcommand (`report`), on Windows |
| 4 | No `--ruleset` passed → resolves to `bytefray-rules-1`, not the production `bytefray-rules-4` | Semantic | All measurement output |

On Windows — this repository's primary development platform — **all six
`btctl.py` subcommands fail.** On Linux, five of six fail. Three of the four
shell wrappers are separately dead, invoking a root-level `python3 main.py`
removed in `0e615d3` (2025-09-29).

Its seven tests pass in **0.06 s** because not one of them starts a subprocess,
invokes the engine, or touches the real repository tree. Two of the seven pin
the *broken* behavior as correct: one asserts the dead `BATTLE_AGENTS_JSON`
name under the title "current environment," and one asserts a command shape
against `ROOT / "sdk" / "tooling" / "build.sh"` — a path deleted in the same
commit that wrote the assertion.

**Recommended disposition: REMOVE (§K),** with the two genuinely-unique
capability concepts (single-elimination brackets, cross-match leaderboard
ranking) recorded as REPLACE-LATER ideas belonging on `TournamentService`, not
on `btctl.py`. This is not recommended because the code is broken; it is
recommended because the product need it once served is now served better,
elsewhere, by shipped code — and because repairing it would require restoring a
new dependency from actively-linted code into the frozen `_legacy/` tree.

---

## B. Baseline

| Check | Result |
|---|---|
| Branch | `v6-research` |
| HEAD SHA | `2ac55bb190b4c91caf78fad3245febad0197aed9` ("Bytefray V6 Phase 2B.1 — Starter-Agent Runtime Integrity") |
| Working tree at start | **Clean** (`git status --porcelain` empty) |
| `origin/v6-research` divergence | **None** — `git rev-parse origin/v6-research` == HEAD after `git fetch --all --prune`; `git status -sb` reports `## v6-research...origin/v6-research` with no ahead/behind |
| Phase 0 / 1 / 2A / 2B.1 committed and synchronized | Yes — `ffcbe9f` (Phase 0), `f86eb2c` (Phase 1), `a8c2164`/`d128fd0`/`06e5def`/`f9a55d7`/`096d9a2` (Phase 2A), `2ac55bb` (Phase 2B.1) all present and matching the remote |
| `main` | **Untouched** — `git rev-parse main` == `git rev-parse origin/main` == `82549f9c3ccbdb2e13b8165b32afef00def4a8f2`, unchanged since Phase 0 |
| Current canonical test count | **3,741 collected** (`python -m pytest --collect-only -q`, per-file counts summed) — reconciles exactly with Phase 2B.1 §137's closing count of 3,741 |
| `engine/tests/test_tournament_btctl.py` | **7 tests, all passing, 0.06 s** |

Phase 1 §2 recorded that `origin/v6-research` did not exist at that time. It
exists now and is synchronized; no discrepancy.

Working tree was re-verified clean at phase close (§14 of this report).

---

## C. Tournament topology

Bytefray contains **four distinct things** that can be called "tournament
functionality." Phase 1's finding concerns only the third.

### C.1 Product tournament functionality — live, shipped, user-invocable

| Component | Path | Evidence |
|---|---|---|
| `bytefray tournament` CLI | `engine/src/battle_engine/tournament_cli.py` | `--help` executes; exposes `--rounds/--seed/--ticks/--arena/--quota/--win-mode/--ruleset/--output/--retry-failed/--quiet`; `--ruleset` offers all 5 selectable identities |
| Subcommand dispatch | `engine/src/battle_engine/command.py:41` | `"tournament", … help="run or resume a native round-robin tournament"` |
| Designer launcher | Tools → Run Tournament… | `docs/TOURNAMENTS.md:62-68` |
| Designer results/history | `app/views/tournament.py`, `app/services/tournament_results.py` | `docs/TOURNAMENTS.md:70-93`; `ARCHITECTURE.md:250-254` |
| Artifact | `tournament.json`, schema `battle2.tournament` v1 | `docs/TOURNAMENTS.md:13-14` |

All four modules ship in the wheel (§H).

### C.2 Tournament engine/library functionality — live, shipped

`engine/src/battle_engine/tournament_service.py:214` (`TournamentService`), a
headless orchestration layer over `NativeMatchService`. Builds a deterministic
round-robin schedule, SHA-256-derives per-match seeds, atomically checkpoints
after every match, verifies entrant IDs/order/seed and replay digests on resume,
and derives standings (`ARCHITECTURE.md:140-146`).

Adjacent but **distinct**: `engine/src/battle_engine/agent_evaluation.py`
(`bytefray agents evaluate`) implements its own pairwise/group multi-entrant
matrices. It is not part of the tournament subsystem and is not affected by any
disposition here — but the concept overlap is a Phase 3 item (§N.1).

### C.3 Tournament build/development tooling — **the subject of this phase**

The root-level `tournament/` tree: 8 tracked files, ~38 KB. Fully inventoried in
§D. Not packaged, not imported, not reachable from any product surface.

### C.4 Historical/experimental tournament material

- `tournament/scripts/{cla-vs-cgpt,round_robin,test_hunter}.sh` — dead wrappers
  (§D, §F.5).
- `tournament/rosters/derived.csv` — a stale derived table referencing
  `agents_tooling/*.asm` by a path prefix (`agents_tooling/…`) that does not
  resolve from any root in the current tree; read by nothing.
- `docs/archive/v5/V5_ALPHA1_PHASE4_TOURNAMENT_UX_COMPLETION.md` — closed
  research record for the *product* feature (C.1), correctly archived.

### C.5 The separation, stated plainly

`docs/TOURNAMENTS.md` draws this boundary itself, twice, in the repository's own
words:

> "The CLI uses the normal writable data root, starter initialization, and agent
> discovery; **it does not use `tournament/scripts/btctl.py`**." (line 42)

> "The older `tournament/scripts/btctl.py` remains a legacy standalone workflow
> and **is not the supported execution path**." (lines 97-98)

---

## D. The `tournament/` subsystem

Complete inventory — `git ls-files tournament/` returns exactly these 8 files.

| File | Bytes | Purpose | Status |
|---|---:|---|---|
| `scripts/btctl.py` | 15,737 | Standalone match-harness controller: 6 subcommands (`build`, `smoke`, `sweep`, `roundrobin`, `elim`, `report`) | **Broken** (§F) |
| `roster.json` | 319 | 6 VM built-ins + 2 custom `.asm` entrants | Readable; customs unbuildable |
| `rosters/default.json` | 319 | Byte-equal copy of `roster.json` | Guarded by a test |
| `rosters/derived.csv` | 197 | Stale derived id/kind/source table | Read by nothing |
| `scripts/smoke.sh` | 244 | Wrapper: `btctl.py build` then `btctl.py smoke` | Inherits failures 1–3 |
| `scripts/round_robin.sh` | 13,369 | Pre-`engine/src` harness | Dead — `python3 main.py` (line 173) |
| `scripts/cla-vs-cgpt.sh` | 6,889 | Pre-`engine/src` harness | Dead — `python3 main.py` (line 91) |
| `scripts/test_hunter.sh` | 1,291 | Pre-`engine/src` harness | Dead — `python3 main.py` (line 35) |

### D.1 `btctl.py` characteristics

- **Language/toolchain:** Python 3, standard library only. Lints clean
  (`ruff check tournament` → "All checks passed!") — it is **not** in
  `pyproject.toml`'s `extend-exclude` list, unlike `_legacy/`. The repository's
  tooling therefore treats it as active code while its documentation calls it
  legacy (§N.3).
- **Entry point:** `python tournament/scripts/btctl.py <subcommand>`; no console
  script, no module entry, no `pyproject.toml [project.scripts]` registration.
- **How it reaches the engine:** subprocess only — `_battle_cmd()` returns
  `[sys.executable, "-m", "battle_engine", "run"]` (`btctl.py:46`), with
  `PYTHONPATH` injected manually (`btctl.py:111-119`) and `cwd=REPO_ROOT`. It
  never imports `battle_engine`.
- **Inputs:** `roster.json`; CLI args; `$BUILD_SH` and `$BATTLE_BIN` overrides.
- **Outputs:** per-match directories under `tournament/results/` (**not**
  gitignored — only `agents_build/` is, `.gitignore:24`), each containing
  `replay.jsonl`, `agents.json`, and the engine-written `summary.json`; plus
  `leaderboard.csv`/`leaderboard.md`.
- **Current caller:** **none.** No import, no test invocation as a subprocess,
  no CI job, no packaging reference, no documentation instruction to run it.
- **Test coverage:** `engine/tests/test_tournament_btctl.py`, 7 tests (§G).
- **Relationship to the main Python application:** consumer-only, across a
  process boundary, through the public `bytefray run` CLI. Nothing in
  `engine/`, `client/`, or `app/` depends on it in either direction.

### D.2 Classification

`tournament/` is **legacy developer tooling** — specifically, a pre-1.0 external
consumer of the CLI. It is not part of the Python runtime (never imported), not
a separately-built artifact (nothing builds it), not a prototype of anything
current, and not an SDK consumer any more (the SDK it consumed is gone). The
closest accurate label is *the original repository's local match-running
harness, retained by inertia.*

---

## E. Historical reconstruction

Six commits have ever touched `tournament/`:

| Commit | Date | Subject | Effect |
|---|---|---|---|
| `dc3dfb1` | 2025-09-29 | chore: scaffold BATTLE2 structure; migrate files | **Introduced** `tournament/` **and** `sdk/`, both in the original migration |
| `0e615d3` | 2025-09-29 | engine: move core.py into battle_engine package | Restructure; root `main.py` ceases to exist — the `.sh` wrappers break here and were never updated |
| `019041d` | — | tournament make demo scripts | Added demo wrappers |
| `22c9369` | 2026-08-07 | fix tournament tooling and restore integration CI coverage | Updated `btctl.py` for the then-current CLI; **"make build-tool discovery lazy and use sdk tooling"**; replaced a machine-specific roster symlink; **created `test_tournament_btctl.py` (+156 lines)** |
| `6feb10b` | 2026-08-13 | fix: wire Agent Params through…; **remove sdk/** | Deleted `sdk/` (135 files, ~640 KB) including its `build.sh`; edited `_find_build_sh()`'s candidate list and the test |
| `75f5a2d` | 2026-09-10 | chore(v5): clean repository and release surface | Last touch |

### E.1 The six-day window

The decisive fact is the interval between the last two substantive commits.
On **2026-08-07**, `22c9369` deliberately wired `btctl.py` to use `sdk/` tooling
and wrote its first test suite. **Six days later**, on **2026-08-13**, `6feb10b`
deleted `sdk/`.

`6feb10b`'s own commit message states what happened, without ambiguity:

> "`sdk/` removed (135 files, ~640KB): a dedicated investigation confirmed it
> was added once during the original repo migration and never touched again,
> `sdk/tooling/` is a byte-identical copy of already-dead
> `_legacy/agents_tooling/` code… **Fixed the one real dependent this had:
> `tournament/scripts/btctl.py`'s `_find_build_sh()` candidate list and its
> test, which now uses an isolated fixture instead of relying on `sdk/`'s real
> presence on disk.**"

This is **evidence, not inference**: the removal was deliberate, the dependency
was known, and the chosen remedy was to make the *test* stop depending on
`sdk/`. The runtime capability was not restored, and the commit does not claim
it was. `build.sh` has existed at exactly one path in the entire history of this
repository — `sdk/tooling/build.sh`, added by `dc3dfb1` and deleted by
`6feb10b` (`git log --all --diff-filter=AD -- "*build.sh"` returns those two
commits and nothing else).

### E.2 Was this ever a supported user-facing deliverable?

**No — and the evidence is direct, not circumstantial.**

| Question | Evidence | Answer |
|---|---|---|
| In the wheel? | `bytefray-5.0.0rc1-py3-none-any.whl`, 215 entries — zero begin with `tournament/`; zero contain `btctl` | No |
| In the sdist? | `bytefray-5.0.0rc1.tar.gz`, 283 entries — zero contain `/tournament/` or `btctl` | No |
| In the Windows installer? | `tools/*.spec` and `tools/installer.iss` — zero matches for `tournament` or `warriors` | No |
| Mentioned in `README.md`, `CHANGELOG.md`, `INSTALL.md`, `ARCHITECTURE.md`, `AGENTS.md`, `CONTRIBUTING.md`? | Zero matches for `btctl`/`tournament/scripts`/`tournament/roster` across all six | No |
| Mentioned in user docs? | Only `docs/TOURNAMENTS.md:42` and `:97-98` — **both of which exist solely to say it is not the supported path** | No |

The only other live mention anywhere is `docs/RUFF_DEBT.md:46`, which records
that a past lint pass fixed 5 `C408` findings in `btctl.py` — a historical
bookkeeping note about work already completed, not a dependency.

**Conclusion (evidence-backed):** `tournament/` remained an internal,
developer-local path for its entire existence. It was never shipped in any
artifact and never advertised in any user-facing document.

---

## F. Failure reproduction

All reproductions were run against the clean tree at `2ac55bb`, with every
output directory redirected into the session scratchpad so that no artifact
landed in `tournament/results/` (which is **not** gitignored). No file was
patched.

### F.1 Failure 1 — missing `build.sh` (hard, deterministic, every platform)

```
$ python tournament/scripts/btctl.py build --out <scratch>/agents_build
FileNotFoundError: build.sh not found. Set $BUILD_SH to an existing path or place build.sh at one of:
 - D:\Projects\BATTLE2\tournament\build.sh
 - D:\Projects\BATTLE2\tournament\agents_tooling\build.sh
 - D:\Projects\BATTLE2\tournament\tools\build.sh
                                                              exit 1
```

Deterministic. **Scope is wider than the `build` subcommand.** `btctl.py:325-326`
runs `if customs: build_customs(customs, ROOT/"agents_build")` unconditionally
before dispatching `smoke`, `sweep`, `roundrobin`, or `elim` — and
`roster.json` always declares 2 customs. So **5 of 6 subcommands abort here**,
before any match runs. Only `report` (which returns at `btctl.py:313-315`,
before `load_roster()`) gets past it.

### F.2 The engine side still works — `build.sh` is not the whole story

Running `btctl.py`'s exact constructed command by hand:

```
python -m battle_engine run --ticks 50 --arena 2048 --win-mode score_fallback \
  --territory-w 1 --territory-bucket 32 --seed 7 --a-type writer --b-type runner \
  --replay <scratch>/writer__vs__runner__seed-7__AB/replay.jsonl
→ Winner: tie; ruleset: bytefray-rules-1                        exit 0
```

Every flag `btctl.py` emits is still accepted (`cli.py:317-363`). This confirms
Phase 1 §6.5's claim that the constructed invocation matches the live CLI —
**independently re-verified here, and correct.**

The engine also writes `summary.json` next to the replay
(`cli.py:724`: `summary_path = replay_path.with_name("summary.json")`), and its
flat compatibility schema (`cli.py:1015-1026`: `version: 2`, `mode: "b2"`,
`seed`, `winner`, `A_score`, `B_score`, `A_alive_ticks`, `B_alive_ticks`,
`A_territory`, `B_territory`) matches `btctl.py:124-139`'s `parse_summary()`
key-for-key, and `winner` is `"A"`/`"B"`/`"tie"` as
`aggregate_leaderboard()` expects.

> **A correction to an inference made mid-investigation, recorded per this
> program's evidence discipline.** Reading `results.py:87-132`'s
> `build_summary()` — whose schema is agent-id-keyed with a nested `agents[]`
> list and has none of the flat `A_*`/`B_*` keys — suggested that `btctl.py`'s
> reporting layer was schema-incompatible with current output. **That inference
> was wrong.** `results.build_summary()` serves a different consumer; the
> `bytefray run` CLI writes its own flat compatibility summary at
> `cli.py:1015`. Running the real pipeline disproved the hypothesis. The
> reporting layer is *not* broken by schema drift, and this report does not
> claim it is.

### F.3 Failure 2 — the environment hook is dead (silent, result-corrupting)

`btctl.py:110` sets `env["BATTLE_AGENTS_JSON"]`. The engine reads **only**
`BYTEFRAY_AGENTS_JSON` (`cli.py:248`, and `cli.py:493` documents it as
precedence step 1). There is no alias, no fallback, and no deprecation shim —
grep for `BATTLE_AGENTS_JSON` across `engine/src` returns zero hits.

This is the mechanism by which custom agents reach the engine at all.
`normalize_player()` (`btctl.py:80-84`) returns, for a built custom agent:

```python
{"name": name, "cli": "runner", "cfg": {"type": "blob", "path": …}}
```

— i.e. the literal placeholder string `"runner"` for `--a-type`, with the real
blob supplied only through the env var (`btctl.py:106`'s own comment: *"Supply
blob config via env hook (engine must honor this)"*).

Because the engine no longer reads that variable, the spec is empty, and
`_resolve_agent()` falls through past step 1 to step 4, "built-in by name" —
resolving the placeholder. **A `chatgpt_hunter` vs `claude_agent` match would
silently execute as `runner` vs `runner`**, while the directory tag, match CSV,
and leaderboard all record the custom names. No error, no warning, wrong data.

**Verified empirically** that the variable name is the operative difference: the
same blob spec under `BYTEFRAY_AGENTS_JSON` runs correctly (§I.3), while under
`BATTLE_AGENTS_JSON` the engine silently ignores it and runs the `--a-type`
built-in. This failure is *latent* — it sits behind failure 1 and would surface
the moment `build.sh` were restored. It is the most dangerous of the four
because its output is plausible.

### F.4 Failure 3 — `report` crashes on Windows (hard, platform-conditional)

`report` is the one subcommand that survives failure 1, and the only one the
test suite exercises end-to-end-ish. Run against the real run tree produced in
§F.2:

```
$ python tournament/scripts/btctl.py report --in <scratch>/repro --csv … --md …
  File "tournament/scripts/btctl.py", line 203, in aggregate_leaderboard
    f.write("| agent | gp | w | l | t | winrate | Δscore | Δterr | survive |\n")
UnicodeEncodeError: 'charmap' codec can't encode character '\u0394' in position 37
                                                              exit 1
```

`btctl.py:202` opens the markdown output with bare `open(out_md, "w")` — no
`encoding=` — and writes `Δ` (U+0394). On a `cp1252` default locale this is a
hard crash. The CSV is written first and **is** correct:

```
agent,gp,w,l,t,winrate,avg_score_diff,avg_terr_diff,avg_survive_ticks
writer,1,0,0,1,0.500,0.00,-16.00,50.0
runner,1,0,0,1,0.500,0.00,16.00,50.0
```

So the aggregation *logic* is sound and schema-compatible; only the markdown
writer is broken. This failure is **new — not reported by Phase 1** — and it
lands on the repository's primary development platform (`CLAUDE.md`:
"Primary development platform here is **Windows**"). On a UTF-8 default locale
(Linux CI) it would not fire; it is platform-conditional, and this report does
not claim otherwise.

Every match subcommand also calls `aggregate_leaderboard(...)` with an `out_md`
as its last action, so this failure would additionally terminate `smoke`,
`sweep`, `roundrobin`, and `elim` on Windows even with failures 1 and 2 fixed.

### F.5 Failure 4 — wrong ruleset (semantic)

`btctl.py` emits no `--ruleset`. The observed resolution is
`ruleset: bytefray-rules-1` — the frozen 1.0 identity — via
`OMITTED_RULESET_CANDIDATES`' fail-closed order (Phase 0 §6), because the
roster's six entrants are native VM built-ins. The current production default is
`bytefray-rules-4`.

This is internally *consistent* — `btctl.py` is a Ruleset-1-era tool with a
Ruleset-1-era roster — but it means that even a fully repaired `btctl.py` would
measure agents under the 1.0 ruleset, not the shipped one. It also exposes only
two entrants (`--a-type`/`--b-type`), while the product supports 3+
(`--c-type`, and `bytefray tournament` takes an arbitrary entrant list).

### F.6 The shell wrappers

`cla-vs-cgpt.sh:91`, `round_robin.sh:173`, and `test_hunter.sh:35` all invoke
`python3 main.py`. `Test-Path D:\Projects\BATTLE2\main.py` → **False**; the root
`main.py` has not existed since `0e615d3` (2025-09-29). These three have been
dead for essentially the entire life of the repository and predate the `sdk/`
issue by ten months. `smoke.sh` calls `btctl.py` directly and so inherits
failures 1–3 instead.

### F.7 Is the missing `sdk/` the root cause?

**No.** It is the first visible failure and the only one Phase 1 found, but it
is one of four, and it is not the deepest. Failures 3 and 4 are independent of
`sdk/` entirely. Failure 2 is an unrelated environment-variable rename
(`BATTLE_*` → `BYTEFRAY_*`) that silently orphaned this consumer. Failure 6
predates `sdk/`'s removal by ten months. Restoring `build.sh` alone would move
the pipeline from "fails immediately" to "**produces confidently wrong
numbers**" — a strictly worse state.

---

## G. Test credibility

`engine/tests/test_tournament_btctl.py` — **7 tests, 7 passed, 0.06 s.** The
runtime is itself evidence: no subprocess is spawned, no match is executed, and
no file outside `tmp_path` is read.

| # | Test | Actually tests | Proves |
|---|---|---|---|
| 1 | `test_import_does_not_resolve_build_tool` | Static structure | Importing the module doesn't eagerly resolve `build.sh`, and `ROSTER` points where expected. Sets `$BUILD_SH` to a **nonexistent** path — so it cannot observe the real tree |
| 2 | `test_report_does_not_load_roster_or_resolve_build_tool` | Mocked behavior | argparse routes `report` to `aggregate_leaderboard` with 3 args. `load_roster`, `_find_build_sh`, **and `aggregate_leaderboard` itself** are all mocked — the real aggregation never runs |
| 3 | `test_default_battle_command_uses_current_source_dispatcher` | **Tautology** | Asserts `_battle_cmd()` returns the exact list `btctl.py:46` is hard-coded to return. Proves nothing about whether that command works |
| 4 | `test_run_game_uses_supported_arguments_and_current_environment` | Mocked behavior | `subprocess.run` monkeypatched, so the engine is never invoked. Asserts flag presence, `cwd`, `PYTHONPATH` — **and that `BATTLE_AGENTS_JSON` parses to the cfg dict** (line 94) |
| 5 | `test_build_script_resolution_prefers_override_then_current_tool` | Mocked behavior | Monkeypatches `module.ROOT` to `tmp_path` and creates a `build.sh` there. Proves the *resolution algorithm*; **structurally cannot observe** that the repository has none |
| 6 | `test_build_customs_uses_current_build_script_contract` | Mocked behavior | Sets `build_sh = ROOT / "sdk" / "tooling" / "build.sh"` (line 119) — a path **deleted in `6feb10b`** — mocks `_find_build_sh` to return it and mocks `subprocess.run`. Asserts a command shape against a tool that does not exist |
| 7 | `test_roster_is_portable_regular_json_file` | File presence | **Genuinely valid.** `roster.json` is a regular file (not a symlink) and equals `rosters/default.json`. Guards the symlink regression `22c9369` fixed |

**Coverage classification:** 2 file-presence/static, 4 mocked-behavior, 1
tautological. **Zero** unit-behavior tests of the aggregation math, **zero**
integration tests, **zero** build tests, **zero** end-to-end tests.

### G.1 What the green tests actually prove

That `btctl.py` is **importable**, that its argparse tree is **well-formed**,
that three of its pure functions **construct the argv and env strings they are
written to construct**, and that `roster.json` is a regular file equal to its
sibling.

### G.2 What they do not prove — the coverage gap

None of the following is covered by any test, which is precisely why all four
failures in §F stayed invisible:

- that `build.sh` exists anywhere (failure 1) — test 5 supplies its own;
- that the environment hook is honored by the engine (failure 2) — test 4
  asserts the *dead variable's* name and calls it "current environment";
- that `aggregate_leaderboard` can write its markdown output (failure 3) — test 2
  mocks the function entirely;
- that the emitted ruleset is the intended one (failure 4);
- that any subcommand completes;
- that the engine accepts the constructed argv (true, but by luck — nothing
  pins it).

### G.3 On whether these are "bad tests"

Per the charter's instruction, they are not bad merely for being non-end-to-end.
Tests 1, 5, and 7 are legitimately-scoped unit tests with deliberate isolation —
test 5's inline comment explicitly explains that it uses a controlled fixture
"not real repository-tree state," which is *good* unit hygiene.

The real defect is narrower and worth stating precisely: **two tests encode the
broken state as the expected state, under names that assert the opposite.**

- Test 4 is named `…uses_current_environment` while pinning
  `BATTLE_AGENTS_JSON`, which the engine stopped reading.
- Test 6 is named `…uses_current_build_script_contract` while pinning
  `sdk/tooling/build.sh`, removed in the very commit that edited this file.

A future reader grepping for confidence finds seven green tests with reassuring
names. That is the mechanism by which "tested but non-functional" persisted —
not the absence of end-to-end coverage, but affirmatively misleading naming over
mocked assertions of removed contracts.

---

## H. Current product dependency

**There is none.** Removing or repairing `tournament/` would affect **nothing**
in the current product. Evidence, by trace rather than by text-search absence:

| Product surface | Implementation traced to | Depends on `tournament/`? |
|---|---|---|
| GUI Tournament (Tools → Run Tournament…) | `app/views/tournament.py` → `app/services/tournament_results.py` → `tournament.json` | **No** — imports are `PySide6.*` + `app.services.tournament_results` only |
| CLI `bytefray tournament` | `command.py:41` → `tournament_cli.py` → `tournament_service.py` → `NativeMatchService` | **No** — imports are 11 `battle_engine.*` modules only |
| `TournamentService` | `tournament_service.py:214` | **No** — imports are 6 `battle_engine.*` modules + stdlib |
| Evaluation | `agent_evaluation.py` (`bytefray agents evaluate`) | **No** |
| 4+ entrant functionality | `tournament_cli.py` (arbitrary entrant list); `--c-type` in `cli.py` | **No** |
| Replay / Replay History | `client/src/battle_client/`, `engine/.../replay_history/` | **No** |
| Tournament results | `tournament.json`, schema `battle2.tournament` v1 | **No** |
| Agent packages | `agent_package.py` | **No** |
| Documented user workflows | `README.md`, `docs/TOURNAMENTS.md`, `docs/AGENT_AUTHORING.md` | **No** — zero `btctl` references outside the two disclaimers |
| Packaging / installer | wheel (215 entries), sdist (283 entries), `tools/*.spec`, `installer.iss`, `MANIFEST.in` | **No** — zero `tournament/` entries in any |
| CI | `.github/workflows/*.yml` | **No** — zero matches for `tournament`/`btctl` |

The direction of dependency is one-way and outward: `btctl.py` consumes the
`bytefray run` CLI as a subprocess. Nothing consumes `btctl.py`.

**Stated explicitly, as §7 requires:** current user-facing tournament
functionality does **not** use the broken `tournament/` subtree. The collision
is nominal. A reader who conflated them would wrongly conclude that Bytefray's
shipped Tournament feature is broken; it is not, and nothing in this phase
suggests it is.

---

## I. `sdk/` dependency analysis

### I.1 What `sdk/` was

Added by `dc3dfb1` (2025-09-29) in the original migration; removed by `6feb10b`
(2026-08-13) — 135 files, ~640 KB, never touched in between. `ARCHITECTURE.md`
had already classified it as inert baggage alongside `_legacy/`.
`sdk/tooling/` contained exactly three files:
`asm_assembler.py`, `build.sh`, `build_wrapper.sh`.

### I.2 What `tournament/` consumed from it

**Exactly one file: `sdk/tooling/build.sh`.** A ~60-line bash script. The
consumed API surface is a 2-positional/6-flag CLI:

```
build.sh SRC.asm OUT.bin --entry N --name NAME [--ptr N] [--src N] [--dst N] [--stride N] [--byte N]
```

`btctl.py:66-76` uses only `--entry` and `--name`. The script `sed`-substitutes
tokens into a temp `.asm`, calls `python3 asm_assembler.py … --entry N`,
validates that every opcode is in `range(0, 12)`, and writes `OUT.bin` plus a
`OUT.bin.meta.json` sidecar.

**Quantified:** 1 file to restore; 1 consuming function (`_find_build_sh`,
`btctl.py:22-40`); 1 call site (`build_customs`, `btctl.py:58`); 2 tests
referencing it (tests 5 and 6, §G); 2 roster entries that need it
(`roster.json`'s `chatgpt_hunter` and `claude_agent`).

### I.3 What replaced it

**Nothing replaced `build.sh`.** But the two capabilities it wrapped are *not*
both gone, and the distinction matters for repair cost:

- **The assembler survives.** `sdk/tooling/asm_assembler.py` and
  `_legacy/agents_tooling/asm_assembler.py` were verified in this phase to be
  **content-identical** (compared directly against `6feb10b^:sdk/tooling/
  asm_assembler.py`). So the real work `build.sh` delegated is still in the
  tree — inside `_legacy/agents_tooling/`, which `pyproject.toml:141`
  **excludes from linting** as frozen dead code.
- **The blob runtime is alive.** Verified by direct execution: with the
  *correct* `BYTEFRAY_AGENTS_JSON` variable and an absolute path, the current
  engine still loads and runs a legacy-assembled blob —
  `_legacy/agents_tooling/chatgpt_hunter.bin` vs built-in `runner` completed
  with `Winner: A` under `bytefray-rules-1`, exit 0. The `type: blob` path
  (`cli.py:506-512`) is fully functional.

So the missing piece is narrowly the **assembly wrapper**, not the assembler and
not the runtime.

### I.4 Would adapting `tournament/` be straightforward or a rewrite?

**Straightforward in code volume; wrong in architecture.** Re-creating
`build.sh` is roughly 60 lines. But:

1. **It would create a new dependency from actively-linted code into
   `_legacy/`.** `btctl.py` is linted as live code; `_legacy/agents_tooling/`
   is deliberately excluded as frozen. Today the only link between them is a
   *data* reference (`roster.json`'s `asm` paths). Repair would add an
   *executable* one — reversing the direction the repository has been moving
   since `6feb10b`.
2. **The script is not portable to the primary platform.** It requires bash
   plus GNU-specific behavior: `sed` `\b` word boundaries (GNU extension),
   `mktemp /tmp/agentXXXX.asm` (hard-coded POSIX path), and `stat -c%s`
   (GNU coreutils; BSD/macOS use `stat -f%z`). On Windows it needs Git Bash,
   and it would still be the only build step in the repository that does.
3. **Prebuilt blobs cannot substitute.** `_legacy/agents_tooling/` contains
   `chatgpt_hunter.bin` but **no `claude_agent.bin`** (only `claude_agent.asm`)
   — verified. So one of the roster's two customs genuinely requires a working
   assembler; shipping prebuilt blobs would not close the gap.
4. **It fixes only failure 1 of four.** Failures 2, 3, and 4 are untouched by
   restoring `build.sh`, and failure 2 becomes *active* rather than latent.

No replacement was implemented, proposed in code, or prototyped in this phase.

---

## J. Disposition alternatives

### A. KEEP AS-IS — rejected

**Evidence for:** the subsystem costs nothing at runtime (never imported, never
packaged); its 8 files are ~38 KB; its tests run in 0.06 s; and it harms no
user, because no user can reach it.

**Evidence against:** it is not inert, it is *actively misleading*. Seven green
tests with names asserting "current environment" and "current build script
contract" stand behind a pipeline where all six subcommands fail on the primary
development platform. `ruff` lints it as live code while `docs/TOURNAMENTS.md`
calls it legacy. Phase 1 §13.2 explicitly declined to recommend this state:
*"Leaving it as-is (tested but broken) is explicitly not recommended by this
audit as a standing state."* This phase found three further failures Phase 1
did not, which strengthens rather than weakens that position.

**Consequence:** the next engineer to grep for tournament confidence finds seven
passing tests and draws a false conclusion — exactly what happened in the
six-day window of §E.1.

### B. REPAIR — evaluated seriously, not recommended

**What a genuine repair requires** (scoped, not implemented):

| Work | Scope |
|---|---|
| Re-create `build.sh` | ~60 lines bash, or a Python port to avoid the GNU/bash dependency |
| Point it at a surviving assembler | `_legacy/agents_tooling/asm_assembler.py` — a new executable dependency into frozen code (§I.4) |
| Fix failure 2 | `btctl.py:110` → `BYTEFRAY_AGENTS_JSON`; fix test 4, which asserts the wrong name |
| Fix failure 3 | `btctl.py:202` → `open(out_md, "w", encoding="utf-8")` |
| Fix failure 4 | Add `--ruleset` plumbing, or accept 1.0-era measurements |
| Wrappers | Delete or rewrite 3 dead `.sh` files (§F.6) |
| Tests | Rewrite tests 4 and 6 (they pin removed contracts); add the integration/build coverage §G.2 shows is absent — otherwise the same regression recurs |

**Evidence for:** the pieces are individually small, the engine side already
works (§F.2), and the blob runtime is alive (§I.3).

**Evidence against — the decisive argument:** repair must be justified by a
product need that nothing else meets. `TournamentService` already meets the
round-robin need, and meets it **better on every axis**: canonical
`battle2.result` v2 artifacts, atomic checkpointing, digest-verified resume,
corruption detection, arbitrary entrant counts, explicit `--ruleset` selection,
GUI integration, replay-history association, and 3 dedicated test modules
(`test_tournament_service.py`, `test_tournament_results.py`,
`test_v5_alpha1_phase4_tournament_results.py`). `btctl.py` offers a
two-entrant, Ruleset-1, no-resume, no-verification subprocess loop.

**Risk:** repairing it re-establishes a second, parallel tournament execution
path with no stable API seam, pointed at frozen `_legacy/` code, which future
phases would then have to maintain or re-retire. Per Phase 0 §14's guiding rule
— *delete before refactoring* — this inverts the intended order.

### C. REMOVE — recommended (see §K, §L)

**Evidence for, against each of the charter's four criteria:**

1. *No longer part of supported product behavior* — `docs/TOURNAMENTS.md:42`
   and `:97-98` say so in the repository's own words (§C.5).
2. *No current artifact depends on it* — zero entries in the wheel (215), the
   sdist (283), every PyInstaller spec, `installer.iss`, `MANIFEST.in`, and
   every CI workflow; zero imports anywhere in `engine/`, `client/`, `app/` (§H).
3. *History/releases already preserve it* — the full tree is recoverable from
   `2ac55bb` and from every prior commit; `build.sh` itself was recovered
   during this phase from `6feb10b^` with a single `git show`, which
   demonstrates the preservation concretely rather than asserting it.
4. *Tests/docs exist only because the subsystem was never removed* — the test
   file was created on 2026-08-07 and orphaned six days later (§E.1); both live
   doc mentions exist solely to disclaim it.

### D. REPLACE / REDESIGN LATER — partially applicable, folded into §K

`btctl.py` does contain **two capability concepts the product genuinely lacks**,
and intellectual honesty requires naming them rather than pretending removal
costs nothing:

- **Single-elimination brackets** (`single_elim`, `btctl.py:225-262`).
- **Cross-match leaderboard ranking** (`aggregate_leaderboard`,
  `btctl.py:153-206`) — win rate, average score differential, average survival.

But `docs/TOURNAMENTS.md:95-97` records both as **deliberate product non-goals**:
*"There is no bracket visualization, parallel scheduler, elimination bracket,
rating system, custom tournament scoring UI…"* And Phase 0 §12 question 7 keeps
ranking systems open as research: *"Evaluation/ranking systems (Elo/Glicko/
TrueSkill-style) remain explicitly not built and not a V6 requirement by
default."*

So these are **not lost functionality** — they are unbuilt ideas that happen to
have a broken sketch in the tree. The sketch has no salvage value: it is
two-entrant, Ruleset-1, and its bracket tally re-scans `summary.json` files by
parsing agent names out of **directory names** (`btctl.py:246-257`), a technique
incompatible with the canonical artifact model `TournamentService` established.

**Determination required by §9.D:** the old implementation should **not** remain
temporarily. Keeping a broken sketch does not make a future feature easier —
`git` preserves it, and a future bracket feature would be built on
`TournamentService`'s canonical schedule and `battle2.result` artifacts, not on
a directory-name parser.

---

## K. Recommended disposition

> ## REMOVE — retire the entire `tournament/` tree and its test file, recording the two unbuilt capability ideas as REPLACE-LATER notes against `TournamentService`.

Justified against the §12 recommendation standard:

| Criterion | Finding |
|---|---|
| **Current product relevance** | None. Never packaged, never shipped, never user-reachable, explicitly disclaimed twice in its own documentation (§E.2, §H) |
| **Actual callers** | Zero. One-way outward consumer of the CLI; nothing consumes it (§D.1) |
| **Compatibility requirements** | None triggered. `AGENTS.md`'s retained-surface rules cover stable protocol identifiers and `battle_engine.core` re-exports — `btctl.py` is neither. It reads no historical artifact and no artifact references it |
| **Repair cost** | Low in lines, high in architecture: a new executable dependency from linted code into frozen `_legacy/`, a non-portable bash/GNU build step on a Windows-primary project, plus rewriting 2 misleading tests and adding the integration coverage that never existed (§J.B) |
| **Ongoing maintenance burden** | Demonstrated, not hypothetical: it has silently absorbed four independent regressions across three unrelated changes (`sdk/` removal, the `BATTLE_*`→`BYTEFRAY_*` rename, the `engine/src` restructure) without one test noticing |
| **Architectural fit** | Poor and worsening. A second tournament execution path with no stable API seam, reaching into the engine via subprocess + `PYTHONPATH` injection + an undocumented env hook |
| **Test credibility** | Actively negative — 2 of 7 tests assert removed contracts under names claiming currency (§G.3) |
| **Historical preservation** | Fully satisfied by git. Demonstrated in this phase by recovering `build.sh` from `6feb10b^` |

Explicitly *not* the reasoning the charter warns against: this is **not** REMOVE
because the code is broken (§12: *"Do not recommend REMOVE merely because code
is broken"*). A broken subsystem serving a live, unmet product need would
warrant REPAIR. The dispositive facts are that the need is **already met, better,
by shipped code** (`TournamentService`), and that the subsystem was **never part
of the product** to begin with — not that it fails.

Equally, this is not KEEP merely because the code exists, and not REPAIR merely
because the tests could be made green.

---

## L. If REMOVE — the dependency-complete removal set

### L.1 Source (8 tracked files — the entire `tournament/` tree)

```
tournament/roster.json
tournament/rosters/default.json
tournament/rosters/derived.csv
tournament/scripts/btctl.py
tournament/scripts/cla-vs-cgpt.sh
tournament/scripts/round_robin.sh
tournament/scripts/smoke.sh
tournament/scripts/test_hunter.sh
```

### L.2 Tests (1 file, 7 tests)

```
engine/tests/test_tournament_btctl.py
```

Canonical collected count moves **3,741 → 3,734**. This fills the gap Phase 1
§12.2 left as *"Unknown (test_tournament_btctl.py func count not separately
tallied)"* — the count is **7**.

### L.3 Documentation (2 edits, both deletions of disclaimer text)

- `docs/TOURNAMENTS.md:42` — drop the trailing clause *"; it does not use
  `tournament/scripts/btctl.py`"*.
- `docs/TOURNAMENTS.md:97-98` — drop the sentence *"The older
  `tournament/scripts/btctl.py` remains a legacy standalone workflow and is not
  the supported execution path."*

Both exist only to disambiguate from the removed tree; with it gone they
reference nothing. The surrounding non-goals sentence (line 95-97) must be
**kept** — it states product scope independently.

### L.4 Configuration (1 line)

- `.gitignore:24` — `agents_build/`, `btctl.py`'s default build output
  directory. Verified referenced by **nothing else** in `pyproject.toml`,
  `pytest.ini`, `tools/`, or `.github/workflows/`.

### L.5 Packaging and CI — no changes required

Verified zero references in the wheel, sdist, all four `tools/*.spec` files,
`tools/installer.iss`, `MANIFEST.in`, and every workflow under
`.github/workflows/`. `pyproject.toml`'s `packages.find` already excludes
`tournament/` structurally. **Nothing to remove.**

### L.6 Local untracked state (not git-visible)

`tournament/scripts/__pycache__/` (gitignored via `.gitignore:2`; contains
`btctl.cpython-{310,311,312,313}.pyc` dating to Aug 2026 — **pre-existing, not
created by this phase**, and left untouched). `tournament/results/` and
`tournament/agents_build/` do not currently exist. A removal pass should delete
the directory wholesale on disk.

### L.7 Explicitly **NOT** in the removal set — a correction to Phase 1

- **`warriors/*.red` — independent; do not couple.** Phase 1's Batch G
  (§11, §12.2, §13.3) groups `warriors/` with `tournament/` as one retirement
  unit. **This phase found no justification for that coupling.** A direct search
  of every file under `tournament/` for the string `warriors` returns **zero
  matches**. `roster.json` references `_legacy/agents_tooling/*.asm`, never
  `warriors/`. The `.red` files are Redcode for the pMARS backend; `btctl.py`
  has no pMARS path. They are two unrelated questions and should be decided
  separately. Phase 1's own §13.3 in fact poses the `warriors/` question on its
  own terms (document a pMARS use, or remove) — that framing is correct and
  stands; only the Batch G packaging is wrong.

- **`_legacy/agents_tooling/` — out of scope here.** `roster.json` is its only
  cross-reference from active code (Phase 1 §10). Removing `tournament/`
  therefore *severs* that link, which simplifies any future `_legacy/` review —
  but `_legacy/` is retained for its own independent reason (frozen
  characterization fixture backing `_legacy/tests/test_smoke.py`,
  Phase 1 §6.2 **KEEP**) and is unaffected.

- **`docs/RUFF_DEBT.md:46` — leave as-is.** It records that a past lint pass
  fixed 5 `C408` findings in `btctl.py`. It is a historical account of completed
  work, not a live reference; editing it would falsify the record. Per this
  program's discipline, historical documents describing what was done at the
  time are not retroactively rewritten.

- **Nothing in `engine/`, `client/`, or `app/`.** No production source file
  participates in this removal.

---

## M. If REPAIR — minimum repair scope (defined, not implemented)

Recorded for completeness should the maintainer choose B over C. The **minimum**
to move from "tested but non-functional" to "honestly functional" — anything
less leaves a worse state than today (§F.7):

1. **Restore the build step.** Port `sdk/tooling/build.sh` (recoverable via
   `git show 6feb10b^:sdk/tooling/build.sh`) to Python to avoid the bash/GNU
   `sed \b`/`stat -c%s`/`mktemp /tmp/...` portability failures on Windows.
   Decide deliberately whether it may depend on
   `_legacy/agents_tooling/asm_assembler.py` or must vendor it out of the
   frozen tree.
2. **Fix the environment hook.** `btctl.py:110` → `BYTEFRAY_AGENTS_JSON`, and
   correct test 4 (line 94), which currently asserts the dead name. **Without
   this, repair produces silently wrong results** (§F.3).
3. **Fix the markdown writer.** `btctl.py:202` → add `encoding="utf-8"`.
4. **Decide the ruleset question.** Either plumb `--ruleset` through, or
   document that `btctl.py` deliberately measures under `bytefray-rules-1`.
5. **Resolve the dead wrappers.** Delete `cla-vs-cgpt.sh`, `round_robin.sh`,
   `test_hunter.sh`, or rewrite their `python3 main.py` invocations.
6. **Add the missing coverage.** At minimum one test that actually executes a
   subcommand end-to-end against a temp output directory. Without it, the §E.1
   regression pattern simply recurs.
7. **Rewrite test 6.** It asserts against `ROOT / "sdk" / "tooling" /
   "build.sh"`, a path that will still not exist after any repair.

Steps 2, 3, and 7 are mandatory in **every** scenario in which the tree is
retained, including KEEP — they are not repair-specific.

---

## N. Phase 3 architecture findings (deferred, not fixed)

1. **Three independent implementations of "every entrant plays every other."**
   `tournament_service.py` (canonical, artifact-backed), `agent_evaluation.py`
   (pairwise/group matrices for `agents evaluate`), and `btctl.py:217-223`
   (dead). Even after removing the third, **two remain**, with overlapping
   scheduling and standings concepts and separate result models. Whether that
   is deliberate layering or unremediated duplication is a Phase 3 boundary
   question. Note Phase 0 §10 and Phase 1 §6.4 both declined to split
   `agent_evaluation.py`; this is a *boundary* question, not a split proposal.

2. **The flat `version: 2, mode: "b2"` compatibility summary is duplicated and
   structurally two-entrant.** Written independently at `cli.py:1015-1026` and
   `agent_test.py:871-881`, both hard-coding slots `A`/`B` only, while the
   product supports 3+ entrants (`--c-type`, and arbitrary entrant lists in
   `bytefray tournament`). Two writers of one undocumented shape, with a
   dimensional limit that predates the current entrant model.

3. **The repository has no consistent marker for "retained but inert."**
   `_legacy/` is ruff-excluded and documented as frozen; `tournament/` is
   ruff-linted as active code while documented as legacy. Tooling and
   documentation disagree, and only the documentation is correct. Whatever
   Phase 2 decides here, the repository would benefit from one explicit
   convention.

4. **No stable API seam for external match harnesses.** `btctl.py` reached the
   engine through subprocess + manual `PYTHONPATH` injection + an undocumented
   environment variable. `NativeMatchService` is the canonical *internal*
   boundary (`ARCHITECTURE.md:54-56`) but is not exposed as a stable external
   contract. If out-of-tree harnesses are ever a goal, that is an API design
   question — and the absence of such a seam is part of why this consumer
   rotted invisibly.

5. **Rename hygiene: the `BATTLE_*` → `BYTEFRAY_*` environment-variable
   migration shipped without an alias, a deprecation warning, or a consumer
   audit.** One consumer was silently orphaned and no test detected it — the
   failure mode was *silent wrong results*, not an error. Worth a standing
   convention for future renames of any externally-observable contract.
   (Phase 1 §6.4's env-var inventory found no *stale flags*; it did not check
   whether any *consumer* still used a pre-rename name. The two audits are
   complementary, not contradictory.)

---

## O. Risks and uncertainties

Stated plainly, per this program's requirement to separate proof from inference.

1. **Failure 2 is established structurally and by targeted experiment, not by
   running a repaired pipeline.** Proven: the engine reads only
   `BYTEFRAY_AGENTS_JSON` (`cli.py:248`, zero repo-wide hits for the old name);
   the blob path works under the correct name (§I.3); `normalize_player` emits
   the literal `"runner"` placeholder. **Not directly demonstrated:** a full
   `btctl.py` custom-agent match silently running `runner` vs `runner`, because
   failure 1 blocks reaching that code path without patching — which this phase
   is forbidden to do. The inference chain is short and each link is verified,
   but it is an inference.

2. **Failure 3 is platform-conditional.** Reproduced on Windows/`cp1252`. On a
   UTF-8 default locale it would not fire. It is not claimed as universal.

3. **The maintainer may hold a private `build.sh`.** `_find_build_sh()` honors
   `$BUILD_SH`, so failure 1 may not affect this machine's owner. Failures 2, 3,
   and 4 would still apply. If such a file exists locally, its content and
   provenance should inform the final decision — this phase could only observe
   the tracked tree. **This is the one open question a human can answer that
   this report cannot.**

4. **No full pytest run was performed** — correctly, per §15 ("No full pytest
   run is required because this phase should not modify executable code"). The
   3,741 figure is a `--collect-only` count reconciled against Phase 2B.1's
   executed run, not an independent pass/fail result. Only
   `test_tournament_btctl.py` (7 passed) was executed.

5. **`019041d`'s diff was not individually inspected** (it is a small
   demo-script addition between two commits whose diffs *were* read). It does
   not bear on any conclusion here.

6. **The §F.2 correction is recorded deliberately.** An early inference from
   `results.build_summary()` — that `btctl.py`'s reporting layer was
   schema-incompatible — was disproved by running the real pipeline and is
   nullified rather than quietly dropped, following the precedent Phase 1 §3
   set with the false `.pyc` claim. Prior reports, including this one, are
   claims to re-verify.

7. **This report re-verified Phase 1's tournament claims rather than inheriting
   them.** Phase 1's core findings held: the `sdk/`/`build.sh` causation, the
   `docs/TOURNAMENTS.md` legacy status, and the CLI-flag compatibility were all
   independently confirmed. Two corrections are recorded: Phase 1 reported one
   failure where four exist (§F), and Phase 1's Batch G incorrectly couples
   `warriors/` to `tournament/` (§L.7).

---

## Appendix: reproduction commands

```bash
git rev-parse HEAD                       # 2ac55bb190b4c91caf78fad3245febad0197aed9
git status --porcelain                   # (clean)
git rev-parse main origin/main           # 82549f9… twice (untouched)
python -m pytest --collect-only -q       # 3,741 collected
python -m pytest engine/tests/test_tournament_btctl.py   # 7 passed in 0.06s

# Failure 1 (deterministic, exit 1):
python tournament/scripts/btctl.py build --out <scratch>/agents_build

# Engine side still works (exit 0) -- btctl's exact constructed argv:
python -m battle_engine run --ticks 50 --arena 2048 --win-mode score_fallback \
  --territory-w 1 --territory-bucket 32 --seed 7 --a-type writer --b-type runner \
  --replay <scratch>/writer__vs__runner__seed-7__AB/replay.jsonl

# Failure 3 (Windows/cp1252, exit 1 after writing a correct CSV):
python tournament/scripts/btctl.py report --in <scratch>/repro \
  --csv <scratch>/repro/leaderboard.csv --md <scratch>/repro/leaderboard.md

# Blob runtime is alive (exit 0, Winner: A) -- note the CORRECT variable name:
BYTEFRAY_AGENTS_JSON='{"A":{"type":"blob","path":"<abs>/_legacy/agents_tooling/chatgpt_hunter.bin","name":"chatgpt_hunter"},"B":{"type":"builtin","id":"runner"}}' \
  python -m battle_engine run --ticks 30 --arena 2048 --seed 7 \
  --a-type runner --b-type runner --replay <scratch>/blobtest/replay.jsonl

# History:
git log --all --oneline -- tournament/            # 6 commits
git log --all --diff-filter=AD --name-status -- "*build.sh"   # only dc3dfb1 (A), 6feb10b (D)
git show 6feb10b^:sdk/tooling/build.sh            # the removed script, fully recoverable
git ls-tree -r --name-only 6feb10b^ -- sdk/tooling/   # 3 files

# Packaging (zero tournament/ entries in either):
python -c "import zipfile; print([n for n in zipfile.ZipFile('dist/bytefray-5.0.0rc1-py3-none-any.whl').namelist() if n.startswith('tournament/')])"
python -c "import tarfile; print([n for n in tarfile.open('dist/bytefray-5.0.0rc1.tar.gz').getnames() if '/tournament/' in n])"
```
