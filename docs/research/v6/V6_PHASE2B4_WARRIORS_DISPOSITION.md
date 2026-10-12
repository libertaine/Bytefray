# Bytefray V6 — Phase 2B.4: `warriors/` Disposition Research

**Phase type:** Research-only. No source, test, packaging, or configuration file
was modified. The only tracked change produced by this phase is this document.

**Governing principle applied:** `warriors/` was evaluated purely on its own
evidence. Its Phase 1 association with the (now-removed) `tournament/` harness
was treated as a known-bad premise and independently re-tested, not inherited.

---

## A. Executive conclusion

`warriors/` is **eight Redcode source files (10,883 bytes total)** vendored in a
single commit on 2025-09-30 alongside the Windows pMARS binaries, and **never
modified since**. It is not code, not a fixture, and not a package input.

The central finding is unambiguous and was verified from several independent
directions:

> **`warriors/` has zero consumers anywhere in the repository.** No production
> module, no test, no GUI path, no packaging manifest, no installer, no release
> script, and no CI workflow reads any file in it. Nothing would stop being
> tested, built, shipped, or executed if the directory vanished today.

Three supporting facts sharpen that conclusion rather than softening it:

1. **The one CI job that runs a real warrior file deliberately does not use
   this corpus.** `.github/workflows/linux-pmars-build.yml` runs
   `validate.red` — but from `$RUNNER_TEMP/pmars-source-one/warriors/`, the
   *upstream pMARS 0.9.5 archive it downloads from SourceForge*, not from the
   repository. The repo holds its own copy of that same file, unused.
2. **The two smoke-test harnesses that need warriors hand-write their own.**
   `tools/smoke_test.sh` generates `imp.red` and `dwarf.red` into a temp
   directory with `;author SmokeTest`; `tools/smoke_after_install.ps1` writes
   two throwaway imps under the data root. The repository therefore contains
   *three independently hand-rolled copies* of the same trivial warriors while a
   tracked corpus of the real ones sits untouched.
3. **A prior V6 pass already cleaned the sibling half of this same import and
   left this half behind.** Commit `06e5def` (V6 Phase 2A.2) trimmed
   `pmars/windows/` from seven files to two — deleting `AUTHORS`, `CONTRIB`,
   `ChangeLog`, `README`, and `pmars-server.exe` — all of which arrived in the
   *identical* commit as `warriors/`. `warriors/` was not considered.

Despite all of that, **this report does not recommend deletion of the whole
directory.** The corpus is live, functional content for a documented and
currently supported product feature. Behavioral testing performed in this phase
(§G.4) confirms six of the eight files assemble and run correctly under the
bundled pMARS at Bytefray's own CLI defaults, and that the full user-facing
`bytefray run --mode redcode94` path produces a valid schema-v2 summary from
them. Meanwhile `README.md`, `docs/MANUAL_SMOKE_TESTS.md`,
`docs/LINUX_INSTALL.md`, and `tools/pmars/README.md` all document that workflow
using **placeholder paths** (`path/to/a.red`, `<warrior-a>`) — and the
repository's only actual answer to "where do I get a warrior file?" is this
directory.

**Recommended disposition: B — KEEP BUT RECLASSIFY, with a partial trim (§L).**
Relocate the material to an explicitly-named examples location with a
provenance/licensing README, drop the two files that are pMARS-internal
artifacts rather than example warriors, and neutralize the commented-out
packaging line that currently makes `warriors/` look like a shipping candidate.

The strongest argument for moving it is not size — 10.9 KB is negligible. It is
that **this directory has already demonstrably caused an incorrect architectural
conclusion**: Phase 1 coupled it to `tournament/` as a single retirement batch
("Batch G"), a coupling Phase 2B.2 had to explicitly refute after finding zero
references between them. A top-level directory that reads as legacy, is named
after a concept Bytefray explicitly disclaims, and has no stated purpose is a
recurring source of exactly that error.

---

## B. Baseline

Established before any investigation began, and re-verified at the end.

| Item | Value |
| --- | --- |
| Branch | `v6-research` — confirmed |
| HEAD SHA | `ac9a998fd54cd5b305af72bfe064105f80d3a3b0` |
| Working tree at start | **Clean** (`git status --porcelain` empty) |
| Divergence from `origin/v6-research` | **0 ahead, 0 behind** (`git rev-list --left-right --count`) |
| Phase 2B.3 committed and synchronized | **Yes** — landed as two commits: `7db15c7` (harness removal, 9 files, −1,143) and `ac9a998` (docs + `.gitignore` + phase report) |
| `main` | `82549f9c3ccbdb2e13b8165b32afef00def4a8f2`, identical to `origin/main` — **untouched** |
| Canonical test count | **3,734 collected** across 158 files (`python -m pytest --collect-only -q`, per-file counts summed) |

The canonical count reconciles exactly with Phase 2B.3's closing figure
(3,712 passed + 22 skipped = 3,734). No drift.

**Note on the Phase 2B.3 commit pair:** the phase is recorded under two commits
sharing one subject line. Both are present on `origin/v6-research` and the
content is complete and non-overlapping (removal in one, documentation in the
other). This is a cosmetic history artifact, not an integrity problem, but it is
recorded here because a reader scanning `git log --oneline` sees an apparent
duplicate.

---

## C. Directory inventory

Eight tracked files, one flat directory, no subdirectories.

| File | Bytes | Lines | Title / `;name` | Stated author | Trailing LF |
| --- | ---: | ---: | --- | --- | --- |
| `aeka.red` | 4,018 | 94 | Aeka | T. Hsu | yes |
| `validate.red` | 2,821 | 117 | Validate 1.1R | Stefan Strack | yes |
| `pspace.red` | 1,510 | 45 | P-space demo | Stefan | yes |
| `flashpaper.red` | 1,095 | 66 | Flash Paper3.7 | Matt Hastings | yes |
| `rave.red` | 784 | 30 | Rave | Stefan Strack | yes |
| `test_eval.red` | 473 | 14 | *(none — not a warrior)* | *(none)* | yes |
| `dwarf.red` | 110 | 6 | Dwarf | A. K. Dewdney | **no** |
| `imp.red` | 72 | 3 | Imp | Unknown | **no** |
| **Total** | **10,883** | **375** | | | |

All eight are plain ASCII, LF-terminated internally (`.gitattributes` sets
`* text=auto eol=lf`). Every file is hand-maintained source text; none is
generated, and none has ever been edited in this repository (§I).

### C.1 Grouping by role

The directory is **not one object**. Three distinct roles live here, which is
why §J classifies at file level rather than directory level.

**Group 1 — Competitive sample warriors (3 files, 5,897 bytes):**
`aeka.red`, `flashpaper.red`, `rave.red`. Real ICWS'94 tournament-grade warriors
with strategy commentary, version histories, and `;assert` guards. `aeka.red`
carries a 20-line changelog and a documented vulnerability analysis. These
demonstrate what the Redcode mode is actually *for*.

**Group 2 — System validators / feature demos (3 files, 4,804 bytes):**
`validate.red` (an ICWS'88 compliance and in-register-evaluation test suite that
self-ties on a compliant simulator and suicides on a non-compliant one),
`test_eval.red` (not a warrior at all — a torture test for pMARS's expression
parser, self-described as *"assertions to test the maths parser of pmars (found
in eval.c)"*), and `pspace.red` (a demonstration of pMARS P-space, explicitly
self-described as *"by no means a competitive warrior"*).

**Group 3 — Minimal classics (2 files, 182 bytes):** `imp.red` and `dwarf.red`.
The canonical one-instruction Imp and Dewdney's Dwarf bomber. These two are
distinguishable from the other six by more than size: they **lack trailing
newlines**, lack `;redcode` dialect headers, lack `;assert` guards, and lack an
`end` directive. That byte-level signature is consistent with their having been
hand-entered rather than copied from the upstream distribution (§I.2).

---

## D. Current consumer map

Method: repository-wide `git grep` for the path `warriors`, then a separate
per-filename search for each of the eight basenames, then manual inspection of
every call path that survived. Raw counts were not trusted — every hit below was
opened and read.

### D.1 Every repository hit for the string `warriors`

| Location | What it actually is | Classification |
| --- | --- | --- |
| `.github/workflows/linux-pmars-build.yml:179` | `warrior="$RUNNER_TEMP/pmars-source-one/warriors/validate.red"` — path inside the **downloaded upstream pMARS 0.9.5 archive** (`PMARS_URL`, unzipped at line 97), not the repo | **Not a consumer** |
| `tools/smoke_test.sh:66,67,126,127` | `prepare_redcode_warriors()` **writes its own** `imp.red`/`dwarf.red` into `${RUN_DIR}/warriors` with `;author SmokeTest` | **Not a consumer** |
| `tools/smoke_after_install.ps1:223` | Creates `"smoke warriors"` under the data root and writes two throwaway imps | **Not a consumer** |
| `pyproject.toml:126` | `# "share/bytefray/warriors" = ["warriors/*"]` — **commented out**, inside a self-labeled illustrative `[tool.setuptools.data-files]` example block | **Not a consumer** (latent hazard — §N.3) |
| `engine/src/battle_engine/cli.py:468` | Help text `"Minimum initial distance between warriors"` for the pMARS `-d` pass-through flag | **Not a consumer** (terminology only) |
| `README.md:400` | Comparison-table prose describing Core War's execution model | **Not a consumer** (terminology only) |
| `docs/AGENT_AUTHORING.md:4`, `docs/specs/agent_validation.md:578` | Prose distinguishing Redcode warriors from Bytefray agents | **Not a consumer** (terminology only) |
| `warriors/pspace.red:32` | A comment inside one of the files themselves | **Not a consumer** |

### D.2 Per-filename search

Searching each basename (`aeka`, `dwarf`, `flashpaper`, `imp`, `pspace`, `rave`,
`test_eval`, `validate`) across all tracked files returned **zero** genuine
references. Every apparent hit was a coincidental substring — `dwarfs` /
`dwarfed` in prose, `traversal` for `rave`, `validates` / `validation` for
`validate`, `import` for `imp`, `test_evaluation_*.py` for `test_eval`. The only
literal `dwarf.red` / `imp.red` occurrences in the repository are the strings
`tools/smoke_test.sh` writes into its own temp directory.

### D.3 Subsystem-by-subsystem

| Subsystem | Finding | Classification |
| --- | --- | --- |
| Production Python (`engine/src`, `app`, `client/src`) | Six `warrior` mentions total, all in `cli.py`'s pMARS flag block (lines 453–468) and one error string (line 738). `--red-a`/`--red-b` have **no default value**; the CLI hard-fails with exit 2 if absent or non-existent (`cli.py:729-739`). No fallback to `warriors/` exists. | **No dependency** |
| `_legacy/` | Contains `*.asm` files in a **Bytefray-native** legacy assembly (`MOV byte`, `MOVP`, `LOADI`, `STOREI`) — not Redcode. Entirely disjoint artifact class. | **No dependency** |
| pMARS integration (`engine/src/battle_engine/pmars.py`) | Resolves and invokes the pMARS executable only. Warrior paths arrive as caller-supplied arguments. | **No dependency** |
| Rulesets | `app/services/ruleset_options.py:119` states outright that Redcode/pMARS *"uses no Bytefray Ruleset at all"* | **No dependency** |
| CLI | See above — user-supplied paths only | **No dependency** |
| GUI / Designer | No Redcode file picker, no `.red` handling, no `--mode redcode94` surface anywhere in `app/` | **No dependency** |
| Evaluation / TournamentService / replay | Redcode mode produces a summary but **no canonical replay** (`cli.py:742-743`); no evaluation or replay path touches warriors | **No dependency** |
| Agent import/export | `docs/specs/agent_validation.md:578` confirms Redcode warriors *"are never entries under `<data_root>/agents/`"* and never reach `discover_agents`/`resolve_agent` | **No dependency** |
| Test fixtures | Zero. `engine/tests/test_pmars.py` writes its own `a.red`/`b.red` containing the literal text `;redcode` into `tmp_path` | **No dependency** |
| Package configuration | Structurally excluded (§F) | **No dependency** |
| Installers | `tools/installer.iss` ships four frozen dists + `README.md` + `LICENSE` only | **No dependency** |
| Docs | Every documented Redcode invocation uses placeholders | **No dependency** (but see §K.E) |
| Research tools (`tools/v3_*`, `tools/spectator_*`) | No Redcode surface at all | **No dependency** |
| Release scripts | `tools/check_wheel.py` guards *against* pMARS material appearing in the wheel; says nothing about warriors | **No dependency** |
| CI workflows | Only the upstream-archive reference above | **No dependency** |

**Result: no consumer in any category.** Not "test-only", not "development-only",
not "ambiguous" — the count is zero across the board.

---

## E. Terminology map

The prompt's caution against treating "warrior" and "agent" as interchangeable is
well-founded: the repository maintains the distinction carefully in prose, and
the distinction is load-bearing.

| Term | Meaning in this repository | Where it lives |
| --- | --- | --- |
| **Warrior** | A Redcode program executed by **external pMARS**, supplied by the user as a `.red`/`.load` file path | `warriors/*.red`; `cli.py` `--red-a`/`--red-b` help text; README's Core War comparison column |
| **Agent** | A Bytefray Python/YAML program implementing `reset`/`declare_processes`/`act` against Agent API v1/v2, discovered under `<data_root>/agents/` | `agents/`, `battle_engine/data/starter_agents/`, the entire native engine |
| **Legacy `.asm` program** | A pre-v0.3 Bytefray-native assembly artifact — **neither** a warrior nor a current agent | `_legacy/agents_tooling/*.asm` |
| **Compatibility fixture** | *(empty category)* — no warrior is used as a fixture by any test | — |
| **Example content** | What `warriors/*.red` functionally is, though nothing in the repository says so | `warriors/` |
| **Research-only content** | *(empty category)* — no experiment consumes these files | — |

`README.md:394` states the boundary explicitly:

> Bytefray takes inspiration from Core War's shared-memory competitive
> programming model but **is not a Redcode implementation or compatibility
> layer**.

`README.md:398` labels the Core War column of its comparison table "Warrior
Code" against Bytefray's "Standard Python classes". The separation is deliberate
and consistently maintained in documentation.

**The leak is structural, not textual.** A top-level directory named `warriors/`
sitting beside `agents/` implies a peer relationship between two things the docs
work hard to distinguish — one is unused vendored third-party sample data for an
external simulator, the other is live first-class runtime content. That is the
context-locality problem (§M) stated in terminology terms.

---

## F. Packaging / release status

Every row below was verified directly against current manifests, and the sdist
row was verified **empirically by building one**, not by reading configuration.

| Channel | Included? | Evidence |
| --- | --- | --- |
| **Wheel** | **No** | `[tool.setuptools.packages.find]` uses `include = ["battle_engine*", "battle_client*", "app*"]` (`pyproject.toml:89-91`). `warriors` matches no pattern and is not a Python package. Not in `[tool.setuptools.package-data]` either. |
| **sdist** | **No — empirically confirmed** | Built `bytefray-5.0.0.tar.gz` (`python -m build --sdist --no-isolation`, output to scratchpad). **283 entries; top-level members are exactly `app/`, `client/`, `engine/`, `bytefray.egg-info/`. Zero `.red` files, zero `warriors` matches.** `MANIFEST.in` contains only `global-exclude *.py[cod]` and `prune tests`. |
| **Windows installer** | **No** | `tools/installer.iss` `[Files]` ships `{#DistRoot}\bytefray\*`, `bytefray-cli\*`, `bytefray-agent-designer\*`, `bytefray-replay-viewer\*`, plus `README.md` and `LICENSE`. Zero matches for `warriors` or `.red`. |
| **Frozen application builds** | **No** | `tools/bytefray_cli.spec` and `tools/bytefray.spec` bundle exactly two pMARS items on Windows — `pmars/windows/pmars.exe` and `pmars/windows/COPYING` — plus the starter-agent data tree. No warrior content. |
| **Published releases** | **No** | `CHANGELOG.md` contains **zero** occurrences of `warrior` or `.red` across the entire release history through v5.0.0 (tags v2.0.0-rc2 … v5.0.0). The corpus has never been announced, documented as a deliverable, or referenced in any release note. |
| **Source checkouts only** | **Yes** | This is the complete set of contexts in which the files exist. |

**Users have never received these files and have never been expected to rely on
them.** The Windows installer's user gets a bundled pMARS *engine* and no warrior
content whatsoever — they must supply their own `.red` files to exercise the mode
the installer just gave them.

Phase 1's claim that packaging structurally excludes `warriors/` was
**independently re-verified here** rather than inherited, and is **confirmed
accurate**, now with empirical sdist evidence Phase 1 did not have.

---

## G. pMARS / compatibility analysis

### G.1 Is `warriors/` required by pMARS execution?

**No.** `engine/src/battle_engine/pmars.py` resolves an executable and runs it.
Warrior paths are caller-supplied. `cli.py:729-739` validates that both
`--red-a` and `--red-b` are given and that both files exist, returning exit 2
otherwise — there is no default and no fallback directory.

### G.2 Is it required by pMARS smoke tests?

**No — and the evidence is unusually direct.** All three smoke paths avoid it:

- `tools/smoke_test.sh` (`prepare_redcode_warriors`, lines 66–92) writes its own
  `imp.red` and `dwarf.red` into `${RUN_DIR}/warriors`.
- `tools/smoke_after_install.ps1` (line ~223) writes `"imp one.red"` and
  `"imp two.red"` under the data root — deliberately using paths with spaces to
  exercise quoting.
- `.github/workflows/linux-pmars-build.yml` uses the **upstream archive's**
  `warriors/validate.red` from the pMARS 0.9.5 zip it downloads and unpacks.

The third case is the sharpest: CI runs *the same file* the repository tracks,
and gets it from SourceForge instead.

### G.3 Redcode compatibility, historical behavior, conversion/import, regression tests

**Not required for any of them.** Bytefray disclaims being a Redcode
implementation or compatibility layer (`README.md:394`). Redcode runs on an
external simulator under no Bytefray Ruleset
(`app/services/ruleset_options.py:119`). There is no Redcode→Bytefray conversion
or import feature anywhere in the tree. `engine/tests/test_pmars.py` (308 lines)
tests executable discovery, quoting, frozen-bundle resolution, error
normalization, and artifact cleanup — all with synthetic inputs, none with
tracked warriors.

### G.4 Behavioral verification (performed in this phase)

Rather than reason from file contents, each warrior was executed against the
**bundled** `pmars/windows/pmars.exe` at **Bytefray's own CLI default
parameters** (`-s 8000 -c 80000 -p 8000 -l 100 -d 100`), paired against
`imp.red`, one round:

| File | Result at Bytefray CLI defaults |
| --- | --- |
| `aeka.red` | Assembles and runs — **wins** (`Aeka by T.Hsu scores 3`, `Results: 1 0 0`) |
| `dwarf.red` | Assembles and runs — ties |
| `flashpaper.red` | Assembles and runs — ties |
| `imp.red` | Assembles and runs — ties |
| `rave.red` | Assembles and runs — ties |
| `validate.red` | Assembles and runs — ties (self-ties, i.e. **reports a compliant simulator**) |
| `test_eval.red` | Assembles with an intentional warning (`Invalid ';assert' parameter` on the deliberate 21-digit literal); behaves as a non-warrior and **loses** |
| `pspace.red` | **Fails to assemble** — `Error in line 10: ';assert VERSION >= 80 && ROUNDS > 1' / Assertion in this line fails` |

`pspace.red` was re-tested at `-r 2` and assembles and runs correctly. Its
failure is therefore a real, reproducible incompatibility with the **Bytefray
CLI's default `--rounds 1`**, not a defect in the file.

The full user-facing path was then exercised end-to-end:

```
bytefray --mode redcode94 --red-a warriors/aeka.red --red-b warriors/rave.red --rounds 3
→ exit 0; runs/_loose/summary.json written
   {"version": 2, "mode": "redcode94", "winner": "A", "backend": {"returncode": 0, ...}}
```

**Conclusion:** the corpus is live, working content — six of eight files are
immediately usable demonstration material for a documented, supported mode, and
the seventh works with one non-default flag. This is the single strongest
argument against treating the directory as inert debris.

### G.5 pMARS version fragmentation (incidental finding)

Three different pMARS versions are implicated by the current tree and its
history:

- **Bundled binary:** `pmars/windows/pmars.exe` self-reports
  `pMARS v0.9.4, 04/07/22`.
- **Linux CI build:** `PMARS_URL` pins `pmars-0.9.5.zip`.
- **Bundled documentation (deleted in `06e5def`):** the `README` added in the
  same commit as the binary was *"README for pMARS version 0.9.0"*.

The bundled README was therefore already mismatched with the binary it shipped
beside. This is recorded for Phase 3 (§N.1), not acted on here.

---

## H. Test-value analysis

**Tests that depend on `warriors/`, directly or indirectly: none.**

The search was run three ways to avoid a false negative: by directory path, by
each of the eight basenames, and by scanning every test file containing `.red`
or `redcode`. That last set is six files — `engine/tests/test_pmars.py`,
`test_cli_agent_listing.py`, `test_cli_characterization.py`,
`test_replay_history.py`, `test_ruleset_persistence.py`, and
`tests/test_v5_replay_history_qualification.py` — and **five of them contain no
`.red` literal at all**; they matched only on the word "redcode" in prose or
parameter names.

The sixth, `engine/tests/test_pmars.py`, constructs its own warriors:

```python
warrior_a = tmp_path / "a.red"
warrior_b = tmp_path / "b.red"
warrior_a.write_text(";redcode", encoding="utf-8")
```

A one-line file whose entire content is `;redcode`. The suite deliberately does
not need real Redcode, because what it tests is executable resolution and process
handling, not Redcode semantics.

> **What would stop being tested if `warriors/` disappeared? Nothing.**

The canonical count would remain 3,734, and no assertion anywhere would change
behavior. Synthetic fixtures could replace the corpus without losing coverage —
because the corpus provides no coverage to lose. The files' value is
demonstrative, not protective, and §J classifies them on that basis.

---

## I. Historical reconstruction

### I.1 Introduction

`git log --follow -- warriors/` returns **exactly one commit**:

```
853d634  2025-09-30  Add sample warriors and bundled pmars binaries (GPLv2)
```

That commit added 15 files in one movement — the seven-file `pmars/windows/`
bundle (`AUTHORS`, `CONTRIB`, `COPYING`, `ChangeLog`, `README`,
`pmars-server.exe`, `pmars.exe`) *and* all eight warriors, 977 insertions total.

The directory has **never been modified since**. No file in it has been edited,
added, renamed, or removed in the ~11.5 months to HEAD. Its role never changed
across V1–V5 because it never had an assigned role to change.

### I.2 Provenance

The evidence establishes that six of the eight files came from the pMARS
distribution itself, alongside the binaries:

- **`test_eval.red`** self-identifies as a test of pMARS's `eval.c` — a file from
  the pMARS *source tree*, meaningless outside it.
- **`pspace.red`** demonstrates *"the new P-space features of pMARS"*.
- **`validate.red`**, **`rave.red`**, and **`pspace.red`** are authored by
  *Stefan Strack* — one of the four named pMARS authors in the `AUTHORS` file
  that arrived in the very same commit.
- **`linux-pmars-build.yml` proves the upstream archive contains a `warriors/`
  directory holding `validate.red`**, by using that exact path after unzipping
  pMARS 0.9.5.
- The commit's own message ties the two halves together under one licence
  notation: *"(GPLv2)"*.

**`imp.red` and `dwarf.red` are the likely exceptions.** Both lack the trailing
newline the other six carry, lack `;redcode` dialect headers, lack `;assert`
guards, and lack `end` directives. That byte-level signature is consistent with
hand entry rather than file copy. Their upstream status is **unresolved** (§O.1).

### I.3 Replacement systems

Bytefray's native engine, Agent API v1/v2, and the `agents/` tree are not
replacements for Redcode warriors — they are a parallel, deliberately different
system (§E). pMARS was retained intentionally as an external backend, and
`tools/pmars/README.md` plus `docs/LINUX_INSTALL.md` document a considered
platform asymmetry (Windows bundles a binary; Linux builds from a
checksum-pinned upstream download). **The pMARS integration is live and
intentional. It simply never wired itself to this corpus.**

### I.4 The decisive historical fact

Commit `06e5def` — *"v6 phase 2A.2 the dead exploratory test + stale CI branch
trigger"* — removed five of the seven `pmars/windows/` files, cutting that bundle
down to `pmars.exe` + `COPYING`. Those five files entered the repository in the
*same commit* as `warriors/`, as part of the *same vendoring act*.

A V6 cleanup pass has therefore already groomed one half of commit `853d634`
while leaving the other half untouched and unexamined. `warriors/` is not
surviving scrutiny — it has been **adjacent to** scrutiny.

---

## J. File / group classifications

Per §9, a mixed result is acceptable, and the evidence produces one. All
classifications are conditional on the recommended relocation in §L.

### KEEP — relocate and document (6 files, 8,900 bytes)

| File | Justification |
| --- | --- |
| `aeka.red`, `flashpaper.red`, `rave.red` | Genuine competitive ICWS'94 warriors with strategy documentation. Verified to assemble and run at Bytefray CLI defaults (§G.4). These are the only content in the repository that meaningfully demonstrates what `--mode redcode94` is for. |
| `validate.red` | ICWS'88 compliance / in-register-evaluation validator. Verified to self-tie (compliant result) against the bundled pMARS. Genuine diagnostic value for verifying a pMARS build — and notably the exact file upstream CI already reaches for. |
| `imp.red`, `dwarf.red` | The canonical minimal pair. Independently corroborated as the *right* choice by the fact that `tools/smoke_test.sh` reinvents precisely these two from scratch. |

### CONSOLIDATE (no file deleted; the duplication is elsewhere)

The repository maintains **three** hand-rolled copies of the imp/dwarf pair: the
tracked `warriors/` versions, `tools/smoke_test.sh`'s inline heredocs, and
`tools/smoke_after_install.ps1`'s two inline imps. Consolidating the smoke
scripts onto a single documented example source is a real simplification — **but
it is deliberately not recommended here**, because both smoke scripts run in
contexts (a temp run dir; a post-install data root on a machine that has no
source checkout) where depending on a repository path would be a regression. The
duplication is defensible; it is recorded so a future pass does not "fix" it
without understanding why it exists.

### EXTRACT / ARCHIVE (1 file, 1,510 bytes)

| File | Justification |
| --- | --- |
| `pspace.red` | Demonstrates pMARS **P-space**, a simulator feature Bytefray exposes through no flag, no CLI surface, and no documentation. It is the one file that **fails to assemble at Bytefray's own default `--rounds 1`** (§G.4). Historically interesting as a pMARS feature demo; not usable example content for a Bytefray user following the documented invocation. |

### DELETE (1 file, 473 bytes)

| File | Justification |
| --- | --- |
| `test_eval.red` | **Not a warrior.** A torture test for pMARS's internal expression parser (`eval.c`), which deliberately emits a malformed-assert warning and deliberately contains an over-long numeric literal. It tests *the simulator's own source*, which Bytefray neither builds on Windows nor modifies. It has no example value, no diagnostic value to a Bytefray user, and no test value here. |

### INVESTIGATE

None. Evidence was sufficient for every file.

---

## K. Disposition alternatives

### A. KEEP AS-IS

- **For:** Zero effort, zero risk, 10.9 KB.
- **Against:** Preserves the exact condition that produced Phase 1's incorrect
  `tournament/`-coupling and that required Phase 2B.2 to spend a section
  refuting it. An unexplained top-level directory named after a concept the
  README explicitly disclaims will keep generating that error. Also leaves the
  commented-out packaging line (§N.3) in place.
- **Verdict:** Rejected — it re-purchases a known, already-realized cost.

### B. KEEP BUT RECLASSIFY — **recommended**

- **For:** Retains all demonstrated value (§G.4) while removing the ambiguity
  that has actually caused harm. Gives the documented Redcode workflow a real
  answer to "where do I get a warrior file?" for the first time. Costs one move
  and one README.
- **Against:** Touches repository layout, so it needs a deliberate target-path
  decision. Non-trivially more work than deletion.
- **Verdict:** Recommended, combined with the §J trim.

### C. PARTIAL REMOVE

- **For:** Drops the two weakest files (§J).
- **Against:** On its own, leaves six files in the same ambiguous top-level
  location — the confusion cost is structural, not proportional to file count.
- **Verdict:** Correct as a *component* of B, insufficient alone.

### D. ARCHIVE / EXTRACT (whole directory)

- **For:** Maximum source-tree clarity.
- **Against:** Contradicts the evidence. Archiving implies the material is
  historical; §G.4 shows it is live content for a currently supported, currently
  documented, currently bundled-on-Windows feature.
- **Verdict:** Rejected — mischaracterizes working content as dead.

### E. COMPLETE REMOVE

- **For:** Strictly justified by the consumer analysis alone — zero consumers,
  zero tests, zero packaging, zero release presence.
- **Against:** Would leave `--mode redcode94` documented in four places, bundled
  with a pMARS binary in the Windows installer, and supported by the CLI, with
  **no example content anywhere in the repository**. The manual smoke test at
  `docs/MANUAL_SMOKE_TESTS.md:465` would still instruct a tester to supply
  `<warrior-a>` and `<warrior-b>`, and the repository would no longer offer any.
  Deleting working demonstration material for a shipping feature to reclaim
  10.9 KB is not what V6's clarity goal is for.
- **Verdict:** Rejected — but see §O.3; this is a legitimate product-policy
  choice if the user decides Redcode examples are not something Bytefray wants
  to carry.

---

## L. Recommended disposition

> **B — KEEP BUT RECLASSIFY, with the §J partial trim.**

Concretely: move the six KEEP files to an explicitly-named examples location,
document their provenance and licensing, drop `test_eval.red`, archive or drop
`pspace.red`, and neutralize the commented-out packaging line.

The reasoning, stated plainly: **the consumer analysis proves `warriors/` is
unreferenced, and the behavioral analysis proves it is not useless.** Those are
different findings, and V6's stated goal — clarity as much as bytes — is served
by fixing the *placement and labeling* problem rather than by destroying
functional content whose only defect is that nobody ever wrote down what it was
for.

The directory's real cost is measurable and already realized: it caused a wrong
architectural conclusion in Phase 1 that a later phase had to spend effort
reversing. Relocation and a README address that cost directly. Deletion also
addresses it, but by discarding the one thing in the repository that makes a
documented, Windows-bundled feature demonstrable.

---

## M. If cleanup is recommended — exact dependency-complete change set

Ordered, and complete. No step depends on anything outside this list.

**1. Create the new location with provenance documentation.**
   - Suggested target: `docs/examples/redcode/` (alternative: `examples/redcode/`).
     The exact path is a layout decision worth confirming before implementation;
     the requirement is that the name state *what the files are* and *which
     system runs them*, which `warriors/` does not.
   - Add a README recording: that these are sample ICWS'94 Redcode warriors for
     the **external pMARS backend**, not Bytefray agents; that they are vendored
     from the pMARS distribution (commit `853d634`, alongside pMARS 0.9.x
     binaries); the named third-party authors; the licensing caveat (§O.2); the
     exact `bytefray run --mode redcode94` invocation; and the `pspace`-style
     `;assert ROUNDS > 1` caveat if that file is retained.

**2. Move the six KEEP files** with `git mv` (preserves history): `aeka.red`,
   `flashpaper.red`, `rave.red`, `validate.red`, `imp.red`, `dwarf.red`.

**3. Delete `warriors/test_eval.red`** (§J — DELETE).

**4. Decide `pspace.red`** (§J — ARCHIVE): either move it with the others and
   document the `--rounds 2` requirement in the README, or drop it. Retaining it
   *without* the documented caveat is the one outcome to avoid, since it fails at
   the CLI's default.

**5. Remove the now-empty `warriors/` directory** (Git removes it implicitly once
   the last tracked file is gone).

**6. Neutralize `pyproject.toml:126`.** The commented-out
   `# "share/bytefray/warriors" = ["warriors/*"]` line will reference a
   nonexistent path after step 5, and is a latent packaging/licensing hazard
   regardless (§N.3). Either delete the line or repoint the illustrative example
   at something real.

**7. Docs pass — additive, no existing instruction is invalidated.** Nothing
   currently references `warriors/` by path, so no documentation *breaks*. But
   `docs/MANUAL_SMOKE_TESTS.md` (pMARS section), `docs/LINUX_INSTALL.md`
   (`path/to/a.red`), and `tools/pmars/README.md` (`warrior-a.red`) should each
   gain a pointer to the new examples location — this is the step that converts
   the move from a tidy-up into an actual improvement for users.

**8. Verification.** `ruff check .` and the canonical `python -m pytest -q` must
   both be unchanged: **3,734 collected, 3,712 passed, 22 skipped**. No test
   references any moved file, so any deviation indicates an unrelated problem.
   Additionally re-run the §G.4 behavioral check against the new paths to confirm
   the examples still work where they now live.

**Dependency completeness:** no code, test, fixture, manifest, spec, installer,
CI job, or script reads these paths (§D), so steps 2–5 cannot break a consumer.
Step 6 is the only one touching a build file, and it edits a comment.

---

## N. Phase 3 findings (deferred — not fixed here)

1. **pMARS version fragmentation.** Bundled Windows binary is v0.9.4; Linux CI
   pins and builds 0.9.5; the bundled README (since deleted) documented 0.9.0.
   Windows and Linux users get different simulator versions with no stated
   compatibility position.

2. **Terminology collision between "warrior" and "agent" is handled in prose but
   not in structure.** The docs draw the line carefully (§E); the directory
   layout blurs it by placing `warriors/` beside `agents/` as apparent peers.

3. **Commented-out packaging directives naming real paths are a latent trap.**
   `pyproject.toml:126` names `warriors/*` as a `data-files` candidate. Phase 1
   correctly read it as an illustrative comment — but it is an illustrative
   comment that, if ever uncommented by someone tidying up, would begin
   redistributing third-party Redcode of undocumented licensing (§O.2) in every
   sdist and wheel. Illustrative examples in build files should not name real
   repository paths.

4. **Example and fixture content has no designated home.** Three hand-rolled
   copies of the same trivial warriors exist (§J — CONSOLIDATE) because there was
   no obvious place to point at. The same question applies to
   `_legacy/agents_tooling/examples/*.asm`.

5. **Top-level directories that are neither packages nor runtime inputs create
   recurring context ambiguity.** `warriors/`, `prompts/`, and `pmars/` all sit at
   the root with no structural signal about their role. `tournament/` was the
   fourth and has been removed. This is the general form of the specific problem
   this phase investigated.

6. **`docs/specs/run_match_pmars.md` is stale** — documents a module path and
   function signature that do not exist (flagged by Phase 1, still unremediated).
   Belongs with the pMARS-boundary work.

7. **Third-party content provenance is undocumented.** `third_party_licenses/`
   covers pMARS itself. Nothing anywhere records where the warriors came from,
   who authored them, or under what terms — which is precisely why this phase had
   to reconstruct it from commit archaeology and file headers.

---

## O. Risks and unresolved questions

1. **`imp.red` and `dwarf.red` provenance is unresolved.** Their byte signature
   (no trailing newline, no `;redcode` header, no `;assert`, no `end`) suggests
   hand entry rather than copying from the upstream archive, but this could not be
   confirmed without fetching pMARS 0.9.x and comparing — outside this
   research-only phase's remit. Both are trivial, universally-known programs
   (Dewdney's Dwarf and the one-instruction Imp), so the practical risk is
   negligible; it is recorded for completeness.

2. **Licensing of the warrior files is not established.** pMARS is
   GPL-2.0-or-later and its licence is preserved in `third_party_licenses/`. The
   warriors are authored by named third parties (T. Hsu, Matt Hastings,
   A. K. Dewdney, Stefan Strack) and their individual terms are stated nowhere —
   not in the files, not in the commit, not in `third_party_licenses/`. **This is
   currently moot because nothing is redistributed** (§F), and the recommended
   disposition keeps it moot. It would become a real blocker for any future
   decision to ship example content, and §M step 1 requires the README to say so
   explicitly.

3. **The keep-versus-delete decision is ultimately a product question this
   research cannot settle.** The technical evidence is complete and points one way
   on facts (zero consumers) and the other way on value (working content for a
   shipping feature). §L recommends reclassification because it captures both. If
   the position is that Bytefray should not carry Redcode example content at all —
   a defensible reading of *"not a Redcode implementation or compatibility
   layer"* — then option E is correct, and §M steps 5–8 apply with steps 1–2
   dropped. **That is a policy call for the user, not a finding.**

4. **The relocation target path in §M step 1 is a suggestion, not a conclusion.**
   `docs/examples/redcode/` versus `examples/redcode/` versus a pMARS-adjacent
   location is a layout question that interacts with the Phase 3 item §N.4 (where
   example content belongs generally) and is better settled there than pre-empted
   here.

5. **No canonical pytest run was performed** — only collection (3,734), per the
   phase constraint that research-only work must not alter executable behavior.
   This is reported as a **collection count**, not as a pass/fail qualification.
   The last full canonical run of record remains Phase 2B.3's
   3,712 passed / 22 skipped / 0 failed.

---

## Compatibility questions — direct answers (§10)

| # | Question | Answer |
| --- | --- | --- |
| 1 | Needed to execute current Bytefray agents? | **No.** Bytefray agents are Python/YAML under `<data_root>/agents/`; the native engine has no Redcode path. |
| 2 | Needed for pMARS support? | **No.** pMARS takes caller-supplied paths; CI uses the upstream archive's copy instead (§G.1–G.2). |
| 3 | Needed for current Redcode compatibility? | **No.** `README.md:394` — Bytefray "is not a Redcode implementation or compatibility layer". |
| 4 | Needed to read or replay historical artifacts? | **No.** Redcode mode emits a summary and **no** canonical replay (`cli.py:742-743`). |
| 5 | Used only by tests? | **No — used by nothing at all**, tests included (§H). |
| 6 | Published to users? | **No.** Absent from wheel, sdist (empirically verified), installer, frozen builds, and every CHANGELOG entry (§F). |
| 7 | Current examples or historical fixtures? | **Current examples in substance, nothing by designation.** They work today (§G.4) but no document, manifest, or test names them. |
| 8 | Would removal break documented workflows? | **No workflow would break** — every documented invocation uses placeholder paths. But removal would leave a documented, Windows-bundled feature with no in-repo example content (§K.E). |
| 9 | Could synthetic fixtures replace them without losing coverage? | **Yes, trivially — because there is no coverage to lose.** Two harnesses already synthesize their own (§G.2). |
| 10 | Would removal alter Bytefray's compatibility promise? | **No.** There is no Redcode compatibility promise to alter. |

---

## Context-locality assessment (§12)

| Dimension | Assessment |
| --- | --- |
| **AI context confusion** | **High — and already realized.** Phase 1 coupled `warriors/` to `tournament/` into a single "Batch G" retirement unit on the strength of thematic adjacency; Phase 2B.2 had to devote a section to refuting it after finding zero cross-references. This is a documented, concrete instance of the directory causing a wrong architectural conclusion. |
| **Developer ambiguity** | **High.** A top-level `warriors/` sitting beside `agents/` invites the reading that they are peer concepts, which the README works explicitly to deny. Nothing in the tree states the directory's purpose. |
| **Package / runtime ambiguity** | **Moderate.** Structurally excluded from every artifact (§F), but `pyproject.toml:126` names it as a packaging candidate in a comment — enough to make a reader pause, and enough to become a real hazard if uncommented (§N.3). |
| **Git noise** | **Negligible.** One commit, never touched since. |
| **Source-tree size** | **Negligible.** 10,883 bytes — roughly 0.01% of the tracked tree by file count (8 of 812). |

The size dimensions are irrelevant; the clarity dimensions are not. This is
precisely the case §12 anticipates — *"a small directory that repeatedly causes
incorrect architectural assumptions can still be worth reorganizing"* — and it is
the basis for recommending relocation (§L) over both retention and deletion.

---

## Verification record

Performed after all investigation, immediately before this document was written
and again after writing it.

| Check | Result |
| --- | --- |
| `git status --porcelain` | Only `docs/research/v6/V6_PHASE2B4_WARRIORS_DISPOSITION.md` (untracked) |
| `git diff` | **Empty** — no tracked file modified |
| `git diff --check` | **Clean** — no whitespace errors |
| Source / test / config files changed | **None** |
| `warriors/` modified, moved, or deleted | **No** — untouched, as required |
| `main` | `82549f9c3ccbdb2e13b8165b32afef00def4a8f2` — unchanged, matches `origin/main` |
| HEAD | `ac9a998fd54cd5b305af72bfe064105f80d3a3b0` — unchanged |
| Temporary files staged | **None** — the sdist build and pMARS runs wrote only to the session scratchpad and to gitignored paths |
| Commit / push performed | **No** — per §17, the report is left in the working tree for review |

**Investigative commands that wrote anything:** `python -m build --sdist
--no-isolation --outdir <scratchpad>` (§F) and the pMARS/CLI executions in §G.4
(`BYTEFRAY_ROOT` pointed at the scratchpad). Both were confirmed not to dirty the
tree — `git status --porcelain` was empty immediately after each.
