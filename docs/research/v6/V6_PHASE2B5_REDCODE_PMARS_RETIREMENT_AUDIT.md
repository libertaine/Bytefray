# Bytefray V6 — Phase 2B.5: Redcode / pMARS Retirement Audit

**Phase type:** Research-only. No source, test, packaging, CI, documentation,
ruleset, or configuration file was modified. The only tracked change produced by
this phase is this document.

**Governing product decision (not re-litigated here):**

> V6 retires Redcode/pMARS support completely. Bytefray V6 supports the Bytefray
> programmable-agent model only. Historical releases and Git history preserve the
> former Redcode compatibility path.

**Audit principle applied:** remove the whole compatibility surface, not merely
the obvious binary and example files — while distinguishing *execution* support
(retired) from *historical-artifact readability* (preserved).

---

## A. Executive conclusion

The complete Redcode/pMARS retirement surface is **narrow, sharply bounded, and
almost entirely uncoupled from current Bytefray-agent behavior.** It is far
smaller than the concept's prominence in the documentation suggests.

The single most important structural fact:

> **Exactly one production module imports the pMARS integration, and exactly one
> function in it consumes the integration.** `engine/src/battle_engine/pmars.py`
> is imported by `engine/src/battle_engine/cli.py` and by nothing else in the
> repository. Every other production mention of Redcode or pMARS — 14 files — is
> a **comment, docstring, or help string**, with two exceptions noted below.

The retirement therefore decomposes into four independent, low-risk workstreams:

| Workstream | Nature | Risk |
| --- | --- | --- |
| Production execution path | Delete 1 module + 4 contiguous blocks in `cli.py` | **Low** — no other caller |
| Packaging / installer | Delete 2 near-identical blocks in 2 PyInstaller specs | **Low** — no test asserts their presence |
| CI | Delete 1 workflow outright | **None** — produces no retained artifact |
| Tracked content | Delete 11 files (binary, 2 licences, 8 `.red`) | **None** — zero consumers (Phase 2B.4) |

Three findings materially shape the implementation phase:

1. **Six CLI options that look generic are Redcode-only.** `--core-size`,
   `--max-cycles`, `--max-processes`, `--max-len`, `--min-dist` and `--rounds`
   are grouped under `cli.py`'s `# ICWS'94 / pMARS backend flags` comment, and
   **every single read of all six in `cli.py` occurs inside the `redcode94`
   branch or in `_pmars_arguments`** (§E.2). Native matches use `--ticks` and
   `--arena` instead. The `--rounds` that survives is a *different flag on a
   different parser* — `tournament_cli.py`'s. Retirement removes **9** options
   from `bytefray run`, not 3.

2. **Historical-artifact readability is already fully independent of pMARS, and
   was proven so behaviorally in this phase (§N.2).** A `redcode94` `result.json`
   reads end-to-end — envelope decode, ruleset provenance (`not_applicable`),
   Replay History indexing (`NOT_PRODUCED`), detail fetch, replay resolution, and
   the GUI's `"N/A"` label — with `battle_engine.pmars` never imported. The
   reader path must therefore be **KEPT**, and the four `test_ruleset_persistence.py`
   Redcode tests are **historical-compatibility coverage, not feature coverage**.
   Deleting them would silently reduce V6's guarantee about V0.3–V5 artifacts.

3. **The GUI and Designer have no Redcode surface whatsoever.** A full sweep of
   `app/` and `client/` for `pmars`, `redcode`, `.red`, `warrior` and `core war`
   returns **two comment lines** in `app/services/ruleset_options.py` and nothing
   else (§F). No control, model, service, mode selector, file filter, error
   string, or command-construction path exposes Redcode.
   `app/services/engine_commands.py` never passes `--mode` at all; it relies on
   the `native` default.

**Quantified surface (§Q):** 6 full text-file removals (1,020 lines, 38,205
bytes), 11 full binary/content removals (197,405 bytes), 161 lines of partial
edits in `cli.py`, and roughly 300 further partial-edit lines across production,
packaging, tooling and documentation. **Total tracked removal: 235,610 bytes.**
Every Windows release drops a further **337,050 bytes** of bundled payload.
Expected canonical test count: **3,734 → 3,713 (−21)**.

There is **one genuine open decision** for Phase 2B.6, and only one: whether
`--mode` disappears entirely or survives as a single-choice/deprecated no-op
(§U.1). Everything else in this audit is determinate.

---

## B. Baseline

Established before any investigation began.

| Item | Value |
| --- | --- |
| Branch | `v6-research` — confirmed |
| HEAD SHA at phase start | `69035f790589f3651c27f660481800e10edd7c56` |
| Working tree at start | **Clean** (`git status --porcelain` empty after the §B.1 commit) |
| Divergence from `origin/v6-research` | **0 ahead, 0 behind** (`git rev-list --left-right --count`) |
| `main` | `82549f9c3ccbdb2e13b8165b32afef00def4a8f2`, identical to `origin/main` — **untouched** |
| Canonical test count | **3,734 collected** across 158 files (`python -m pytest --collect-only -q`, per-file counts summed) |
| GUI-marked suite (excluded from the canonical run) | 3 collected; **zero** Redcode/pMARS coverage |

### B.1 Phase 2B.4 synchronization (precondition of §1)

At session start the tree was **not** clean: it held one untracked file,
`docs/research/v6/V6_PHASE2B4_WARRIORS_DISPOSITION.md`. This was **expected
dirt**, not an integrity problem — Phase 2B.4 was research-only and its own §17
instructed it to leave the report uncommitted for review. Nothing was stashed,
discarded, or normalized.

Because this phase's §1 requires Phase 2B.4 to be *committed and synchronized*
before work begins, the report was committed and pushed as-is, matching the
established research-doc commit pattern (`5f7f188`, Phase 2B.2):

- Before: `ac9a998fd54cd5b305af72bfe064105f80d3a3b0`
- Phase 2B.4 commit: `69035f790589f3651c27f660481800e10edd7c56`
- `origin/v6-research` after push: `69035f79…` — **0 ahead, 0 behind**

The canonical count of **3,734** reconciles exactly with Phase 2B.4's closing
figure and with Phase 2B.3's (3,712 passed + 22 skipped). **No drift.**

---

## C. Product policy

Redcode/pMARS retirement is recorded here as an **intentional V6 product
decision**, made before this audit and not a conclusion drawn from it. This
phase did not evaluate whether Redcode support is worth keeping; it was
instructed that the decision is made, and asked only to map the dependency
surface that implements it.

Two consequences of that framing govern every classification below:

- **`warriors/` is in scope by policy, not by evidence.** Phase 2B.4's
  evidence-based recommendation was *B — KEEP BUT RECLASSIFY*. That
  recommendation is **superseded**: the corpus exists solely to feed the retired
  feature, and §J finds no file with an independent non-Redcode role.
- **Retirement targets support claims and active implementation guidance, not
  project lineage.** Bytefray's Core War inspiration is real history and stays
  (§K.3). The goal is that no V6 surface *claims or attempts* Redcode execution.

---

## D. Runtime topology

The complete current execution path for
`bytefray run --mode redcode94 --red-a A --red-b B`.

### D.1 Entry and dispatch

| Step | Location | Behavior |
| --- | --- | --- |
| 1. Console script | `pyproject.toml [project.scripts]` | `bytefray` → `battle_engine.command:main`; `bytefray-cli` → `battle_engine.cli:main` |
| 2. Subcommand routing | `command.py:37-39` | `run` subparser, `help="run a native Bytefray or pMARS match"` — **the only Redcode text in `command.py`** |
| 3. Argument parsing | `cli.py:445-470` | `--mode`, `--red-a`, `--red-b`, `--core-size`, `--max-cycles`, `--max-processes`, `--max-len`, `--min-dist`, `--rounds` |
| 4. Config construction | `cli.py:~690-724` | **Shared with native.** `Config`/`Weights` are built *before* the mode branch and are then entirely unused by it |
| 5. Path resolution | `cli.py:~725` | `_resolve_replay_path`, `summary_path`, `_resolve_trace_path` — **shared with native** |
| 6. Mode branch | `cli.py:727` | `if args.mode == "redcode94":` — the single dispatch point |

### D.2 Inside the branch (`cli.py:727-830`, 104 lines)

| Step | Lines | Behavior | Redcode-only? |
| --- | --- | --- | --- |
| Warrior validation | 729-739 | Requires both `--red-a`/`--red-b`; `exit 2` on a missing file | **Yes** |
| Stale-artifact cleanup | 741-744 | Unlinks a prior `replay.jsonl` / `result.json` | **Yes** |
| Argument construction | 746-757 → `_pmars_arguments` (53-81) | Builds `-b -r -s -c -p -l -d A B` | **Yes** |
| Executable resolution | `pmars.py:107-154` | `PMARS_CMD` → resource root → data root → `PATH` | **Yes** |
| Subprocess invocation | `pmars.py:197-248` | `subprocess.run`, no shell, 30 s default timeout | **Yes** |
| Result parsing | `pmars.py:164-194` | Four fallback regex formats → `"A"`/`"B"`/`"tie"` | **Yes** |
| Error normalization | `pmars.py:22-66` | `PMarsError` and four subclasses → `exit_code` | **Yes** |
| Summary normalization | `cli.py:766-789` | `summary.json` `version: 2`, `mode: "redcode94"`, null score fields | **Yes** |
| Result envelope | `cli.py:790-821` | `stable_id` match/result IDs; `schema_version=SCHEMA_VERSION_V1`; `backend={"name": "pMARS", …}`; `replay=None` | **Yes** |
| Replay generation | — | **None.** Redcode produces no canonical replay | n/a |
| Platform handling | `pmars.py:18-19, 80-96, 99-104` | `os.name == "nt"` gates the `pmars.exe` name and the `pmars/windows` search directory | **Yes** |

### D.3 Shared-versus-exclusive verdict

**Nothing in `pmars.py` serves native execution.** The module's 255 lines are
100% Redcode.

Within `cli.py`, the branch consumes four shared helpers — `_resolve_replay_path`,
`stable_id`, `write_json_atomic`, and `ResultEnvelope` — all of which have
multiple native callers and **all of which stay**. The branch itself has no
native reader.

Three shared *writers* become single-purpose-dead once the branch goes:

- `ResultEnvelope.backend` — **the pMARS path at `cli.py:817` is its only writer
  anywhere in the repository**, and it has **no semantic reader at all** (only the
  serialization passthrough at `result_model.py:180` and the decode at `:255`).
- `termination_reason="backend_completed"` — one writer (`cli.py:812`),
  documented at `docs/RESULT_SCHEMA.md:271-276` as deliberately outside the
  native enum.
- `SCHEMA_VERSION_V1` as a *write* target (`cli.py:820`) — after retirement
  **no code writes a v1 result**, though v1 remains a supported *read* version.

All three must be **kept in the reader**, and are recorded as Phase 3 findings
(§T).

---

## E. CLI / UI surface

### E.1 Current `bytefray run` help (verbatim excerpt)

```
[--mode {native,redcode94}] [--red-a RED_A]
[--red-b RED_B] [--core-size CORE_SIZE]
[--max-cycles MAX_CYCLES] [--max-processes MAX_PROCESSES]
[--max-len MAX_LEN] [--min-dist MIN_DIST]
[--rounds ROUNDS] [--quiet]
...
  --mode {native,redcode94}
                        Engine mode: 'native' for Bytefray (default) or
                        'redcode94' to run pMARS.
  --red-a RED_A         Warrior A file (.red or .load) for redcode94 mode
  --red-b RED_B         Warrior B file (.red or .load) for redcode94 mode
  --core-size CORE_SIZE
                        ICWS'94 core size
  --max-cycles MAX_CYCLES
                        Max cycles per round
  --max-processes MAX_PROCESSES
                        Max processes per warrior
  --max-len MAX_LEN     Max warrior length
  --min-dist MIN_DIST   Minimum initial distance between warriors
  --rounds ROUNDS       Number of rounds to run
```

### E.2 Disposition of every option

| Option | `cli.py` line | Every read is… | Disposition |
| --- | --- | --- | --- |
| `--mode` | 446-451 | the branch test at `:727` | **REMOVE** (see §U.1) |
| `--red-a` | 452-454 | `:729, :733` | **REMOVE WITH FEATURE** |
| `--red-b` | 455-457 | `:729, :734` | **REMOVE WITH FEATURE** |
| `--core-size` | 458 | `:750, :777` | **REMOVE WITH FEATURE** |
| `--max-cycles` | 459 | `:751, :768, :778, :813` | **REMOVE WITH FEATURE** |
| `--max-processes` | 460-462 | `:752, :779` | **REMOVE WITH FEATURE** |
| `--max-len` | 463 | `:753, :780` | **REMOVE WITH FEATURE** |
| `--min-dist` | 464-469 | `:754, :781` | **REMOVE WITH FEATURE** |
| `--rounds` | 470 | `:755, :782` | **REMOVE WITH FEATURE** |
| `--quota` | elsewhere | native `Config.instr_per_tick` | **KEEP** |
| `--ticks`, `--arena` | elsewhere | native | **KEEP** |

**Proof that the six "generic-looking" flags are Redcode-only:** a search of
`cli.py` for `core_size|max_cycles|max_processes|max_len|min_dist|args.rounds`
returns exactly 14 hits — six in `_pmars_arguments`'s signature, six at the
`:750-755` call site, and the remainder at `:768-782` and `:813`, all inside the
branch. No native code path reads any of them.

**`--rounds` disambiguation (important — do not remove the wrong one):** there are
two unrelated `--rounds` flags. `cli.py:470` (`bytefray run`) is Redcode-only and
goes. `tournament_cli.py:45` (`bytefray tournament`) is native and **stays** — it
is what `docs/TOURNAMENTS.md:36`, `app/services/designer_workflows.py:419`,
`test_command.py:172`, `test_launchers.py:101`, `test_starter_agents.py:272`, and
`test_tournament_service.py:157,179` all use.

### E.3 Other CLI surfaces

| Surface | Finding |
| --- | --- |
| Subcommand help | `command.py:38` — `"run a native Bytefray or pMARS match"` → **PARTIAL EDIT** |
| Enum values / argparse choices | Only `--mode`'s `choices=["native", "redcode94"]` |
| Shell completion | **None exists** in the repository |
| Aliases | **None** — `redcode94` has no alias |
| Hidden / deprecated options | **None** |
| Defaults | `--mode` defaults to `native`; removing the flag changes no default behavior |
| `--mode native` callers | **Zero** anywhere in the repository — nothing would break on removal |

---

## F. GUI / Designer surface

**Explicit statement, as §6 requires: no GUI or Designer functionality exposes
Redcode or pMARS in any form.**

A sweep of `app/` and `client/` for `pmars`, `redcode`, `.red`, `warrior`, and
`core ?war` returns exactly **two lines**, both comments:

```
app/services/ruleset_options.py:119-120
# entrants. Deliberately says nothing about Redcode/pMARS, which uses no
# Bytefray Ruleset at all (docs/RULES.md's "Redcode/pMARS -- not Ruleset
```

Confirmed absent:

| Candidate surface | Finding |
| --- | --- |
| Redcode mode selector | **None.** `app/services/engine_commands.py:55-80` never emits `--mode`; it relies on the `native` default |
| `.red` file selection / filter | **None** |
| pMARS options / settings | **None** |
| Redcode agent type | **None** — the Designer catalog is Python/VM only |
| Redcode-specific error messages | **None** — `PMarsError` never reaches `app/` |
| Redcode workflow affordances | **None** |

**Two GUI labels exist because of Redcode but are not Redcode-specific and must
stay** (§N): `app/services/replay_history_presentation.py:197` renders
`"not_applicable"` as `"Not applicable to this match type"` (and `"N/A"` at
`:309`), and `:111,120,1064` render `ReplayState.NOT_PRODUCED` as
`"Not produced"` / `"This workflow did not produce a Bytefray replay."` Both are
already phrased generically and remain correct for historical rows.

---

## G. Production dependency map

### G.1 REMOVE WITH FEATURE — full file

| File | LOC | Bytes | Justification |
| --- | ---: | ---: | --- |
| `engine/src/battle_engine/pmars.py` | 255 | 8,839 | 100% pMARS. Sole importer is `cli.py` |

Public surface lost: `DEFAULT_TIMEOUT_SECONDS`, `PMarsError`,
`PMarsNotFoundError`, `PMarsExecutionError`, `PMarsTimeoutError`,
`PMarsOutputError`, `PMarsResult`, `resolve_pmars_command`, `parse_pmars_winner`,
`run_pmars`.

### G.2 REMOVE WITH FEATURE — partial, `engine/src/battle_engine/cli.py`

| Block | Lines | Count |
| --- | --- | ---: |
| `from battle_engine.pmars import PMarsError, run_pmars` | 27 | 1 |
| `_pmars_arguments()` | 53-81 | 29 |
| `# ICWS'94 / pMARS backend flags` … `--rounds` | 445-470 | 26 |
| `if args.mode == "redcode94": … return 0` | 727-830 | 104 |
| `from battle_engine.result_model import SCHEMA_VERSION_V1 as …` | 29 | 1 |
| **Total** | | **161** |

The `SCHEMA_VERSION_V1` import at `:29` has its only use at `:820`, inside the
branch, so it goes with it.

### G.3 PARTIAL EDIT — help / comment text only

| File | Line(s) | Content | Action |
| --- | --- | --- | --- |
| `engine/src/battle_engine/command.py` | 38 | `help="run a native Bytefray or pMARS match"` | **User-facing — must change** |
| `engine/src/battle_engine/match_service.py` | 4 | Docstring: "…CLI parsing, pMARS, and external result persistence remain outside this native boundary" | Reword |
| `engine/src/battle_engine/result_model.py` | 121-125, 279-281, 349, 367 | Comments plus two error strings "(e.g. a pMARS match)" | Reword; **keep the logic** |
| `engine/src/battle_engine/rules.py` | 144-146 | Comment on `not_applicable` | Reword; **keep the Literal** |
| `engine/src/battle_engine/replay.py` | 146-147 | Comment | Reword |
| `engine/src/battle_engine/replay_history/models.py` | 50-52 | `ReplayState` docstring | Reword; **keep the enum member** |
| `engine/src/battle_engine/replay_history/discovery.py` | 555-556 | Comment | Reword; **keep the branch** |
| `engine/src/battle_engine/tournament_service.py` | 184-188 | Comment | Reword |
| `engine/src/battle_engine/ruleset_policy.py` | 347 | Comment, "locality has no VM/Redcode implementation" | Reword (optional) |
| `app/services/ruleset_options.py` | 119-121 | Comment | Reword (optional) |

### G.4 KEEP — no change

| File | Line | Why |
| --- | --- | --- |
| `engine/src/battle_engine/result_model.py` | 287-288 | `if envelope.mode == "redcode94": return RulesetProvenance(None, "not_applicable")` — **historical-artifact reader**, proven pMARS-independent (§N.2) |
| `engine/src/battle_engine/rules.py` | 147 | `RulesetConfidence` includes `"not_applicable"`; consumed by `replay_history/query.py:47,240` and `app/services/replay_history_presentation.py:197,309` |
| `engine/src/battle_engine/replay_history/models.py` | 60, 326 | `ReplayState.NOT_PRODUCED`; consumed by `service.py:89,530` and four presentation sites |
| `engine/src/battle_engine/data/starter_agents/hunter/agent.py` | 5 | "the classic Redcode-bomber idea of aggression" — design-rationale prose, no support claim |
| `engine/src/battle_engine/data/benchmarks/v3_phase2_locality_corpus.json` | — | Frozen research corpus; prose only; must not be edited |
| `engine/src/battle_engine/paths.py` | — | **Zero** pMARS references, despite being one of `linux-pmars-build.yml`'s path filters |
| `engine/src/battle_engine/core.py`, `__init__.py` | — | **Zero** pMARS re-exports; `__all__ = ["cli"]` |

---

## H. Packaging and installer impact

### H.1 What actually ships today — verified against built artifacts

| Vehicle | Contains pMARS? | Evidence |
| --- | --- | --- |
| Windows frozen `bytefray` | **Yes** | `dist/windows/bytefray/_internal/pmars/windows/{pmars.exe,COPYING}` — 168,525 B |
| Windows frozen `bytefray-cli` | **Yes** | `dist/windows/bytefray-cli/_internal/pmars/windows/{pmars.exe,COPYING}` — 168,525 B |
| Windows installer (Inno Setup) | **Yes, implicitly** | `installer.iss:67-68` copies both dist trees with `recursesubdirs` — **no explicit pMARS line to edit** |
| Windows portable ZIP | **Yes** | Same dist trees |
| Python wheel | **No** — and actively asserted | `check_wheel.py:94-103` rejects any `pmars` path except `battle_engine/pmars.py` |
| Source distribution | **No** | `packages.find` includes only `battle_engine*`/`battle_client*`/`app*`; `pmars/`, `warriors/`, `third_party_licenses/` are structurally excluded |
| Linux release archive | **No** | `bytefray.spec:56` gates on `sys.platform == "win32"`; `build_linux.sh` has zero pMARS references |
| `.red` files, any vehicle | **No** | Never packaged. The `pyproject.toml:126` data-files line is commented out and was never activated |

### H.2 Exact entries to change

| File | Lines | Change |
| --- | --- | --- |
| `tools/bytefray.spec` | 10 | Delete `pmars_dir = …` |
| `tools/bytefray.spec` | 44-54 | Delete the 11-line pMARS rationale comment |
| `tools/bytefray.spec` | 56-62 | Delete the `if sys.platform == "win32"` bundling block |
| `tools/bytefray_cli.spec` | 9 | Delete `pmars_dir = …` |
| `tools/bytefray_cli.spec` | 16-18 | Reword the cross-reference comment (it also covers `starter_agents`) |
| `tools/bytefray_cli.spec` | 20-26 | Delete the bundling block |
| `tools/check_wheel.py` | 75 | `ALLOWED_PMARS_PATHS = {"battle_engine/pmars.py"}` → `frozenset()` — **keep the guard at `:94-103` permanently** |
| `pyproject.toml` | 16 | `keywords = […, "pmars", …]` — remove `"pmars"` (a PyPI **support claim**); `"corewar"` may stay as lineage (§U.3) |
| `pyproject.toml` | 99-100 | Reword "pMARS binaries and third-party licenses are release inputs…" |
| `pyproject.toml` | 122-127 | Delete the commented-out `data-files` example naming `warriors/*` and `third_party_licenses/*` |

`tools/agent_designer.spec` and `tools/replay_viewer.spec` contain **no** pMARS
references. `MANIFEST.in`, `installer.iss`, `build_win.ps1` and `build_linux.sh`
require **no** edits.

### H.3 Tracked content removals

| Path | Bytes | Class |
| --- | ---: | --- |
| `pmars/windows/pmars.exe` | 150,528 | Bundled GPL binary |
| `pmars/windows/COPYING` | 17,997 | pMARS GPL-2.0-or-later text |
| `third_party_licenses/pmars-GPL-2.0-or-later.txt` | 17,997 | **Byte-identical duplicate** of the above (SHA-256 `58530d09…5455`) |

Both `pmars/` and `third_party_licenses/` become **empty and should be deleted
entirely** — `third_party_licenses/` contains this one file and nothing else.

---

## I. CI impact

### I.1 `.github/workflows/linux-pmars-build.yml` — **FULL REMOVE** (250 lines)

| Question (§8) | Answer |
| --- | --- |
| What does it build? | pMARS 0.9.5 from the SourceForge archive (`PMARS_URL`, SHA-256-pinned via `PMARS_SHA256`), built **twice** and byte-compared for reproducibility |
| Is any resulting artifact used elsewhere? | **No.** There is no `upload-artifact` step; line 250 asserts *"No pMARS source or binary is retained or uploaded by this workflow."* |
| Does any current release depend on it? | **No.** `linux-package.yml` builds and uploads the Linux release archive and has zero pMARS references |
| Does it validate the *bundled* pMARS? | **No.** It validates an **upstream-built Linux** binary. The bundled Windows `pmars.exe` is never exercised here |
| Does it use the repository's `warriors/`? | **No.** `:179` uses `$RUNNER_TEMP/pmars-source-one/warriors/validate.red` — the *downloaded upstream archive's* copy. This confirms Phase 2B.4 §A.1 |
| Obsolete after retirement? | **Entirely.** Its final five steps (`:168-250`) exist only to run `bytefray run --mode redcode94` |

Removed with it: `PMARS_URL`, `PMARS_SHA256`, the ELF-dependency and GLIBC-floor
gates, and the nine-entry `paths:` filter (present twice) naming `pmars.py`,
`test_pmars.py`, `build_pmars_linux.sh`, and `tools/pmars/README.md`.

### I.2 Other workflows

| Workflow | pMARS steps | Redcode matrix | Redcode path filters | Caches / artifacts | Verdict |
| --- | --- | --- | --- | --- | --- |
| `ci.yml` | One indirect: `:63` runs `check_wheel.py` (a **negative** pMARS assertion) | None | None | None | **KEEP** — update `ALLOWED_PMARS_PATHS` only |
| `linux-package.yml` | None | None | None | None | **KEEP unchanged** |
| `linux-gui-smoke.yml` | None | None | None | None | **KEEP unchanged** |

**Net CI effect: one workflow deleted, zero steps edited in surviving workflows,
one constant edited in a tool `ci.yml` invokes.**

---

## J. Warriors and `.red` files

### J.1 Complete `.red` inventory

A repository-wide search confirms **all eight tracked `.red` files live in
`warriors/`; there are none anywhere else.** (`.red` files under `build/` and
`work/` are untracked, gitignored smoke-run output.)

| File | Bytes | Phase 2B.4 behavioral finding | V6 disposition |
| --- | ---: | --- | --- |
| `aeka.red` | 4,018 | Runs correctly | **REMOVE WITH FEATURE** |
| `validate.red` | 2,821 | Runs correctly; the CI job uses the **upstream** copy, not this one | **REMOVE WITH FEATURE** |
| `pspace.red` | 1,510 | Requires multiple rounds | **REMOVE WITH FEATURE** |
| `flashpaper.red` | 1,095 | Runs correctly | **REMOVE WITH FEATURE** |
| `rave.red` | 784 | Runs correctly | **REMOVE WITH FEATURE** |
| `test_eval.red` | 473 | Not a warrior — a pMARS **parser torture test** | **REMOVE WITH FEATURE** |
| `dwarf.red` | 110 | Runs correctly | **REMOVE WITH FEATURE** |
| `imp.red` | 72 | Runs correctly | **REMOVE WITH FEATURE** |
| **Total** | **10,883** | | **Delete `warriors/` entirely** |

### J.2 Independent non-Redcode role: none found

§10 directs retention only where *direct evidence* shows an independent role.
Re-verified in this phase against Phase 2B.4's conclusion:

- **Zero consumers.** No production module, test, GUI path, packaging manifest,
  installer, release script, or CI workflow reads any file in `warriors/`.
- **Not a fixture.** The two smoke harnesses that need warriors hand-write their
  own: `tools/smoke_test.sh:72-91` generates `imp.red`/`dwarf.red` with
  `;author SmokeTest`; `tools/smoke_after_install.ps1:225-228` writes two
  throwaway imps under the data root.
- **Never shipped.** No packaged release has ever contained these files
  (`pyproject.toml:126` is a commented-out, never-activated intent).

**Conclusion: the entire `warriors/` tree is a Redcode-support artifact.** It is
preserved by Git history and by every historical release. Per §10, the files are
not retained merely because they still run.

### J.3 Classification of the non-`warriors/` `.red`-adjacent content

| Item | Class | Disposition |
| --- | --- | --- |
| Heredoc warriors in `tools/smoke_test.sh:72-91` | Generated smoke fixture | Removed with the test function (§O.2) |
| Inline warriors in `tools/smoke_after_install.ps1:225-228` | Generated smoke fixture | Removed with the block (§O.2) |
| `linux-pmars-build.yml:222-223`'s deliberately-invalid `invalid.red` | CI fixture | Removed with the workflow |
| Redcode snippets inside `docs/archive/**` | Archived historical evidence | **KEEP** — §11 forbids deleting archived history over embedded snippets |

---

## K. Documentation impact

### K.1 REMOVE / REWRITE — current documentation implying V6 support

| File | Line(s) | Claim |
| --- | --- | --- |
| `README.md` | 130 | "`battle2.result` (schema v2 native JSON; v1 historical/pMARS)" — v1 stays for history; drop the pMARS clause |
| `README.md` | 347 | "`bytefray run`: Execute native matches **or pMARS ICWS'94 benchmarks**" |
| `README.md` | 462 | "pMARS Redcode uses a separate backend and does not execute under a Bytefray ruleset" |
| `README.md` | 550 | "**pMARS Interoperability**: … Distributions bundling pMARS preserve licensing materials in `third_party_licenses/`" — **becomes false** once nothing bundles pMARS |
| `INSTALL.md` | 17, 51 | "their adjacent DLLs, Qt plugins, resources, **and pMARS files** are required" |
| `SECURITY.md` | 53-54, 74-76 | Redcode agents "are executed via an external pMARS process"; the `PMARS_CMD` threat note |
| `AGENTS.md` | 99-106 | The pMARS packaging rule, the GPLv2 preservation requirement, and "Ubuntu pMARS build/runtime" in the CI description |
| `ARCHITECTURE.md` | 53, 133-137, 298-300, 337, 351-352, 361, 379 | The `redcode94` dispatch description, the diagram's `--> pMARS (redcode94 only…)` edge, the CI list, and the artifact line |
| `docs/AGENT_AUTHORING.md` | 4-5, 14, 107, 609 | "…and Redcode warriors through the separate pMARS backend"; the agent-kind table row; `bytefray run --mode redcode94` |
| `docs/LINUX_INSTALL.md` | 118-137 | The whole Linux-pMARS paragraph **and its worked `PMARS_CMD=… --mode redcode94` example** |
| `docs/MANUAL_SMOKE_TESTS.md` | 461-466 | The entire "## pMARS / Redcode integration" procedure |
| `docs/MANUAL_SMOKE_TESTS.md` | 489 | "run native **and bundled-pMARS** matches" |
| `docs/COMPATIBILITY.md` | 47 | "(with v1 retained for historical artifacts and pMARS)" → historical artifacts only |
| `docs/COMPATIBILITY.md` | 763-766 | "**pMARS interoperability continues**" — directly contradicts the V6 decision |
| `docs/RULES.md` | 484-492 | The "### Redcode/pMARS — not Ruleset v1" section and its `--mode redcode94` instruction (but see §U.3) |
| `docs/RULES.md` | 10, 45, 275, 375 | Cross-references into that section |
| `docs/FUTURE_PLANS.md` | 446-450 | "Redcode/pMARS interoperability **is not cancelled**" — must become a retirement statement |
| `docs/RESULT_SCHEMA.md` | 5, 22, 66 | Present-tense writer claims — reframe as historical |
| `docs/TOURNAMENTS.md` | 95-96 | "…or pMARS tournament division" — stays true; drop the mention |
| `docs/specs/run_match_pmars.md` | whole file | **FULL REMOVE** — see §K.4 |

### K.2 KEEP — historical-artifact reader documentation

`docs/RESULT_SCHEMA.md` and `docs/COMPATIBILITY.md` are **compatibility
documents**: much of their Redcode content explains how to *read* artifacts V6
can no longer *produce*. That content stays true and must survive, reframed from
present to past tense but not deleted:

- `COMPATIBILITY.md:650-679` — the `null`-versus-absent `ruleset_id` analysis.
- `COMPATIBILITY.md:737` — the matrix row
  `| result.json | redcode94/pMARS | not_applicable |`. **Stays exactly true.**
- `RESULT_SCHEMA.md:83-95, 118` — the `resolve_result_ruleset` contract.
- `RESULT_SCHEMA.md:271-276` — why `backend_completed` sits outside the native
  enum.
- `docs/REPLAY_SCHEMA.md:206` — "…or never existed (pMARS)".

### K.3 KEEP HISTORICAL / KEEP AS CONTEXT

| File | Line(s) | Class |
| --- | --- | --- |
| `CHANGELOG.md` | 434, 476, 520, 559, 620-622, 1615, 1914, 2013, 2470-2588 | **KEEP HISTORICAL** — prior release entries; §13 forbids rewriting them |
| `docs/archive/**` (34 files) | — | **KEEP HISTORICAL** — archived research |
| `docs/releases/V4_0_0_ALPHA1_RELEASE_REPORT.md` | — | **KEEP HISTORICAL** |
| `docs/ROADMAP.md` | 108-116, 829, 865, 899, 1036-1216 | **KEEP HISTORICAL** — closed roadmap items and shipped-release records; a new V6 entry supersedes them (§U.3) |
| `README.md` | 392-406 | **KEEP AS CONTEXT** — the "Bytefray vs. Core War" table *already asserts Bytefray is not a Redcode implementation*; line 406's "pMARS binaries" describes **Core War's** ecosystem, not Bytefray's |
| `pyproject.toml` | 11 | **KEEP AS CONTEXT** — "inspired by Core War" |
| `docs/PROJECT_HISTORY.md` | 4 | **KEEP AS CONTEXT** — "Core War-inspired engine" |
| `docs/specs/agent_*.md` (7 files) | scope-exclusion lines | **KEEP** — "Redcode scaffolding is out of scope" stays true; `agent_validation.md:578` and `agent_lab.md:130,216,259` may be reworded |
| `tools/research/v5/r4_agents/v5r4_core_warden/` | — | **False positive** — "Core Warden" is a Bytefray agent name, unrelated to Core War |

### K.4 `docs/specs/run_match_pmars.md` — already stale

This spec documents a module `engine/src/battle_engine/backends/pmars.py` and a
function `run_match_pmars(…)` that **do not exist** — verified: there is no
`backends/` directory, and no `run_match_pmars` symbol anywhere in the codebase.
Phase 1 flagged this (its §L, "Batch L") as a doc-reconciliation task.

**Retirement resolves it by deletion rather than reconciliation**, closing an
open Phase 1 item at zero cost.

---

## L. `_legacy/` impact

**Explicit finding: `_legacy/` has zero Redcode/pMARS coupling.**

A search of all 23 tracked `_legacy/` files for `pmars`, `redcode`, `warrior`,
`corewar`, and `core war` returns **no matches at all**.

| Classification | Files |
| --- | --- |
| REMOVE WITH REDCODE | **none** |
| REVIEW (mixed purpose) | **none** |
| KEEP | **all 23** |

`_legacy/` is the pre-v0.3 Bytefray VM lineage — `.asm` sources, `.bin` blobs and
their `.meta.json` manifests, plus `core.py`/`agents.py`/`main.py`/`renderers.py`
and one characterization test. It is an entirely separate legacy axis from
Redcode, and §14's caution against wholesale deletion is moot here: **Phase 2B.6
must not touch `_legacy/` at all.**

---

## M. Ruleset relationship

Explicit answers to §15's four questions:

**1. Does any ruleset require Redcode execution?** **No.** `ruleset_policy.py`
registers `bytefray-rules-1`, `-2-alpha1`, `-2-alpha11`, `-2`, `-3-alpha1`,
`-4-alpha1`, `-4-alpha2`, and `-4`. None invokes, references, or depends on
pMARS. The file's only Redcode mention is a comment at `:347` ("locality has no
VM/Redcode implementation and is not being given one").

**2. Does `bytefray-rules-1`, `2`, `3-alpha1`, `4`, or any alias invoke or imply
pMARS?** **No.** Not one imports `battle_engine.pmars` — `cli.py` is the sole
importer. `supported_runtime_kinds` admits only `"python"` (and implicitly
`"vm"` for v1); **there is no `"redcode"` runtime kind anywhere.**

**3. Is `redcode94` an execution mode rather than a Bytefray ruleset?**
**Yes, unambiguously.** It is a value of `--mode` (`cli.py:448`), parallel to
`native` — a *backend selector*, never a ruleset identity. `--ruleset` is a
separate flag with an entirely disjoint value set. `docs/RULES.md:484-492`
already states this ("No Redcode/pMARS artifact is, or should be described as,
using Bytefray Ruleset v1"), and `result_model.py:287-288` enforces it in code
by returning `not_applicable`.

**4. Would removing pMARS change replay/schema compatibility for Bytefray-agent
matches?** **No.** pMARS produces no canonical replay at all (`replay=None`).
Native replay writing, `battle2.replay` v3/v4, and `battle2.result` v2 are
untouched. The only schema-adjacent consequence is that **no code will write a
`battle2.result` v1 envelope any more** — v1 remains in
`SUPPORTED_SCHEMA_VERSIONS` as a read version, and `ResultEnvelope.schema_version`
keeps `SCHEMA_VERSION_V1` as its dataclass default (`result_model.py:136`), which
several unrelated tests rely on.

**No ruleset is added, removed, renamed, or re-pointed by this retirement.**
`bytefray-rules-3-alpha1`'s separate review is entirely unaffected.

---

## N. Replay and persisted-artifact implications

### N.1 The execution / readability split

| Capability | After retirement |
| --- | --- |
| **Execute** a `.red` warrior | **Gone.** Historical Redcode matches are no longer reproducible in V6 |
| **Open / inspect** a historical `redcode94` `result.json` | **Preserved** |
| **Replay** one | n/a — pMARS never produced a replay; the correct answer is and remains `NOT_PRODUCED` |
| **Render** one in the GUI | **Preserved** — `"Not produced"`, `"N/A"` |
| **Summarize** one | **Preserved** |
| **Migrate** one | **Preserved** — v1 stays readable |

### N.2 Behavioral proof (executed in this phase)

A historical `redcode94` `result.json` — written exactly as `cli.py:766-821`
writes one (`schema_version: 1`, `mode: "redcode94"`, `replay: null`,
`backend: {"name": "pMARS"}`) — was placed under an isolated `BYTEFRAY_ROOT` and
read back through the full current stack:

```
READ OK       : redcode94 1 winner= A
RULESET PROV  : RulesetProvenance(value=None, confidence='not_applicable')
HISTORY ROW   : replay_state= ReplayState.NOT_PRODUCED ruleset_conf= not_applicable
DETAIL        : True
RESOLVE REPLAY: ReplayResolution(state=<ReplayState.NOT_PRODUCED>, path=None, ...)
GUI LABEL     : ruleset= N/A
battle_engine.pmars in sys.modules? -> False
subprocess used? modules with pmars: []
```

**`battle_engine.pmars` was never imported.** Result decode, ruleset provenance,
Replay History indexing, detail fetch, replay resolution, and GUI label rendering
are all structurally independent of the pMARS module.

**Conclusion: retirement can preserve read-only handling of historical records in
full while removing execution support, and requires no compatibility shim to do
so.** The only requirement is negative: do not delete `result_model.py:287-288`,
the `"not_applicable"` `RulesetConfidence` literal, or `ReplayState.NOT_PRODUCED`.

---

## O. API / config / environment impact

### O.1 Public / semi-public API

| Symbol | Disposition | Note |
| --- | --- | --- |
| `battle_engine.pmars` (module) | **Disappears completely** | Importable today but **not documented API**: absent from `battle_engine.__init__.__all__` (`["cli"]`) and from `battle_engine.core`'s re-exports. **Incidental importability only** |
| `PMarsError` + four subclasses | Disappear | Never escape `cli.py`; never reach `app/` |
| `PMarsResult` | Disappears | |
| `resolve_pmars_command`, `run_pmars`, `parse_pmars_winner` | Disappear | |
| `cli._pmars_arguments` | Disappears | Private |
| `ResultEnvelope.backend` | **Loses its only writer; keep the field** | Historical artifacts carry it |
| `"backend_completed"` | **Loses its only writer; keep reader tolerance** | |
| `SCHEMA_VERSION_V1` | **Keep** | Ceases to be a write target; remains a read version and the dataclass default |
| `RulesetConfidence["not_applicable"]`, `ReplayState.NOT_PRODUCED` | **Keep** | §N |

**No documented, supported API is broken.** The compatibility surfaces
`CLAUDE.md`/`AGENTS.md` call out — `battle_engine.core` re-exports and stable
protocol identifiers — contain nothing pMARS-related.

### O.2 Environment, config, and tooling

| Item | Location | Disposition |
| --- | --- | --- |
| `PMARS_CMD` | `pmars.py:115,119,128,129,151` | **Dead — remove.** The repository's only pMARS environment variable |
| `PMARS_CMD` documentation | `SECURITY.md:76`, `LINUX_INSTALL.md:119,136`, `MANUAL_SMOKE_TESTS.md:463`, `tools/pmars/README.md:66,70` | Remove with their sections |
| `PMARS_URL`, `PMARS_SHA256` | `linux-pmars-build.yml:31-32` | Removed with the workflow |
| `EXPECTED_PMARS_C_SHA256` | `build_pmars_linux.sh:7,53` | Removed with the file |
| Executable search paths | `pmars.py:84-96` — `<resource>/pmars/windows`, `<data>/pmars/windows`, `<resource>/pmars`, `<data>/pmars`, `<data>/bin` | **Dead — remove.** `paths.py` itself defines none of these |
| Platform overrides | `pmars.py:18-19, 81, 101, 140` (`os.name == "nt"`) | Removed with the module |
| Installer-created directories | `installer.iss:62-64` creates only `agents` and `runs\_loose` | **No change needed** |
| `tools/build_pmars_linux.sh` (84 lines) | — | **FULL REMOVE** |
| `tools/pmars/README.md` (100 lines) | — | **FULL REMOVE**; `tools/pmars/` becomes empty |
| `tools/smoke_test.sh` | `:5, :12, :28-34` (config), `:66-92` (`prepare_redcode_warriors`), `:119-142` (`test_2_redcode_pmars`), `:190` (call site) | **PARTIAL** — roughly 55 lines; renumber "[2/3]" → "[1/2]" etc. |
| `tools/smoke_after_install.ps1` | `:157-165` (bundled-resource assertion), `:223-247` (match plus invalid-`PMARS_CMD` cases) | **PARTIAL** — roughly 34 lines |

§18's "no dormant pMARS configuration" requirement is fully satisfiable: after
these edits **no pMARS environment variable, search path, or config key remains
anywhere in the repository.**

---

## P. Licensing implications

| Item | Today | After retirement |
| --- | --- | --- |
| `pmars/windows/pmars.exe` | GPL-2.0-or-later binary shipped in every Windows artifact | **Not distributed** |
| `pmars/windows/COPYING` | GPL text shipped beside it | **Removable** — required only because the binary shipped |
| `third_party_licenses/pmars-GPL-2.0-or-later.txt` | **Byte-identical duplicate** (SHA-256 `58530d09…5455`) | **Removable**; the directory becomes empty and goes too |
| Bytefray's own `LICENSE` | Permissive, © 2025 Rod Satterfield | **Unchanged — do not touch** |

**Obligations discharged.** Bytefray currently distributes a GPL-2.0-or-later
binary alongside permissively-licensed software and must preserve its licensing
material (`AGENTS.md:100-103`, `README.md:550`, `ARCHITECTURE.md:338`). Once no
pMARS code or binary ships, that entire obligation — and the written-offer /
source-availability policy sketched at `tools/pmars/README.md:79-100` — lapses.
This is a **real simplification of Bytefray's distribution posture**, not
housekeeping.

**Latent ambiguity removed.** Phase 2B.4 §J recorded that the eight `.red`
warriors carry **no stated licence or provenance anywhere** — not in the files,
not in the importing commit, not in `third_party_licenses/`. They are attributed
to named authors (A. K. Dewdney, Stefan Strack, Matt Hastings, T. Hsu) with no
grant of any kind. Deleting them removes that unresolved question rather than
leaving it to be rediscovered. **No licence text needs to be written.**

---

## Q. Quantified removal estimate

Counts are measured, not estimated. Partial-edit line counts are exact where a
block is contiguous and approximate (`~`) where interleaved prose is involved.

### Q.1 Full file removals — 17 files

| Category | Files | Lines | Bytes |
| --- | ---: | ---: | ---: |
| Production | 1 (`pmars.py`) | 255 | 8,839 |
| Test | 1 (`test_pmars.py`) | 308 | 12,302 |
| CI | 1 (`linux-pmars-build.yml`) | 250 | 9,215 |
| Tooling | 2 (`build_pmars_linux.sh`, `tools/pmars/README.md`) | 184 | 7,282 |
| Docs | 1 (`docs/specs/run_match_pmars.md`) | 23 | 567 |
| Binary | 1 (`pmars.exe`) | — | 150,528 |
| Licence | 2 (`COPYING`, `pmars-GPL-2.0-or-later.txt`) | — | 35,994 |
| `.red` warriors | 8 (`warriors/*`) | 375 | 10,883 |
| **Total** | **17** | **1,395** | **235,610** |

Empty directories also removed: `pmars/windows/`, `pmars/`,
`third_party_licenses/`, `tools/pmars/`, `warriors/`.

### Q.2 Partial edits to mixed-purpose files

| File | Lines removed | Nature |
| --- | ---: | --- |
| `engine/src/battle_engine/cli.py` | **161** | Four contiguous blocks plus two imports |
| `tools/smoke_test.sh` | ~55 | Four blocks |
| `tools/smoke_after_install.ps1` | ~34 | Two blocks |
| `tools/bytefray.spec` | 19 | Three blocks |
| `tools/bytefray_cli.spec` | 11 | Three blocks |
| `pyproject.toml` | ~8 | Keyword plus two comment blocks |
| `tools/check_wheel.py` | 1 | Constant edit (keep the guard) |
| `engine/src/battle_engine/command.py` | 1 | Help string |
| Nine further production files | ~25 | Comments and docstrings only |
| **Production / tooling subtotal** | **~315** | |
| Documentation (19 live files) | ~150 | See §K.1 |
| **Total partial** | **~465** | |

### Q.3 Other dimensions

| Dimension | Count |
| --- | ---: |
| Production files removed entirely | **1** |
| Production LOC removed | **~442** (255 + 161 + ~26) |
| Test files removed entirely | **1** |
| Test cases removed | **21** |
| CI workflows removed | **1** (of 4) |
| CI steps edited in surviving workflows | **0** |
| Documentation files affected | **19 live** (+ 1 removed) |
| Documentation files deliberately untouched | **~40** (`docs/archive/**`, `docs/releases/**`, `CHANGELOG.md` history) |
| Binaries removed | **1** (150,528 B) |
| Licence files removed | **2** (35,994 B) |
| `.red` files removed | **8** (10,883 B) |
| Packaging entries removed | **6** spec blocks + 3 `pyproject.toml` edits |
| Installer entries removed | **0 explicit** (payload shrinks implicitly) |
| Environment variables removed | **1** (`PMARS_CMD`) + 3 CI/script constants |
| Executable search paths removed | **5** |
| **Tracked bytes removed** | **235,610** |
| **Windows release payload removed** | **337,050** (168,525 × 2 frozen trees) |

### Q.4 Expected canonical test count

| | Tests |
| --- | ---: |
| Baseline | 3,734 |
| − `engine/tests/test_pmars.py` (full file, 21 cases) | −21 |
| **Expected after retirement** | **3,713** |

**This assumes the §N historical reader is preserved.** If Phase 2B.6 instead
deletes `result_model.py:287-288`, four further tests in
`test_ruleset_persistence.py` die (→ 3,709) **and V6 loses its guarantee that
historical Redcode artifacts remain readable.** That is a regression, not a
saving. No other test file loses a case; the remaining Redcode references are
fixture data or assertions that survive an edit (§I of the test detail below).

### Q.5 Test-file classification (§9)

| File | Behavior class | Action | Cases lost |
| --- | --- | --- | ---: |
| `engine/tests/test_pmars.py` | Executable discovery (11), subprocess construction (2), execution/error normalization (5), CLI mode behavior (2), GUI-subprocess failure (1) | **Remove entire file** | **21** |
| `engine/tests/test_ruleset_persistence.py:77,82,94,110` | **Backward compatibility** — historical artifact readability | **Keep unchanged** (reword docstrings only) | 0 |
| `engine/tests/test_replay_history.py:432,434,1089,1398,1400` | Generic — `redcode94` used as a fixture mode to reach `NOT_PRODUCED` | **Keep**; optionally retire the literal | 0 |
| `tests/test_v5_replay_history_qualification.py:65` | Same; also outside `testpaths` (not in the canonical run) | **Keep** | 0 |
| `engine/tests/test_designer_workflows.py:204` | Generic — foreign `mode: "pmars"` fixture | **Keep** | 0 |
| `engine/tests/test_cli_characterization.py:37` | CLI mode behavior — asserts `"--mode {native,redcode94}"` in help | **Edit the assertion** | 0 |
| `engine/tests/test_cli_agent_listing.py:56-69` | **Negative** — the legend must never mention Redcode/pMARS | **Keep unchanged** (becomes more true) | 0 |
| `engine/tests/test_install_docs_consistency.py:33` | Comment only | **Keep** | 0 |
| `engine/tests/test_windows_packaging_spec.py` | Packaging — asserts only *positive* `datas` membership | **Keep unchanged** — no test asserts pMARS presence | 0 |
| `engine/tests/test_check_wheel.py` | Packaging — synthetic wheel, no pMARS assertion | **Keep unchanged** | 0 |

---

## R. Dependency-complete implementation batches

Derived from actual dependency direction: `cli.py` → `pmars.py`; specs →
`pmars/windows/`; CI → `cli.py` + `pmars.py` + `build_pmars_linux.sh`;
documentation → everything. Nothing depends on `warriors/`, so it may move freely.

| # | Batch | Contents | Why here | Verify |
| --- | --- | --- | --- | --- |
| **0** | Inventory snapshot | Record HEAD, `git status`, the canonical count 3,734, and the `test_pmars.py` case list. No file changes | §1 baseline for comparison; nothing to prove yet | `pytest --collect-only` |
| **1** | CI first | Delete `.github/workflows/linux-pmars-build.yml` | It references files later batches delete. Removing it first means **no batch ever leaves CI pointing at a missing path** | Workflow list |
| **2** | Tests | Delete `engine/tests/test_pmars.py`; edit `test_cli_characterization.py:37` | Must precede production removal, or batch 3 leaves a red suite | `pytest` → **3,713** |
| **3** | Production | Delete `pmars.py`; remove the four `cli.py` blocks plus two imports; edit `command.py:38` | The core removal, now unreferenced by tests or CI | `pytest`, `ruff check .`, both `mypy` runs, `bytefray run --help` |
| **4** | Packaging | Edit both specs, `check_wheel.py:75`, `pyproject.toml` | Depends on `pmars.py` being gone so `ALLOWED_PMARS_PATHS` is correct | `test_windows_packaging_spec.py`, wheel build + `check_wheel.py` |
| **5** | Binaries and licences | Delete `pmars/`, `third_party_licenses/` | **Must follow batch 4** — deleting first would make the specs' `os.path.isdir` guard fail silently | Windows frozen build |
| **6** | Warriors and tooling | Delete `warriors/`, `tools/build_pmars_linux.sh`, `tools/pmars/`; edit `smoke_test.sh`, `smoke_after_install.ps1` | Independent of everything above; grouped for one reviewable content commit | Smoke scripts parse |
| **7** | Documentation | §K.1's live files plus deletion of `docs/specs/run_match_pmars.md` | Last, so prose describes the finished state | `test_install_docs_consistency.py` |
| **8** | Changelog | New V6 entry (§S.3) | Records the completed retirement | — |
| **9** | Qualification | §S | Nothing left to change | Full §S |

**Review ergonomics.** Batches 1, 2, 5, and 6 are near-pure deletions and review
in minutes. Batch 3 is the only one needing careful reading — keep it to exactly
the four `cli.py` blocks plus `pmars.py`, with **no opportunistic tidying**, so
the diff reads as "this block, verbatim, is gone." Batch 7 is large but
mechanical.

**A defensible four-commit compression**, if fewer commits are wanted:
(1+2+3) *retire the Redcode execution path*; (4+5) *stop shipping pMARS*;
(6) *remove Redcode content and tooling*; (7+8) *documentation and changelog*.

---

## S. Qualification plan for Phase 2B.6

### S.1 Must prove — positive

| Check | Command / method | Expected |
| --- | --- | --- |
| Canonical suite | `python -m pytest` | **3,713** collected; 0 failed, 0 errors |
| Lint | `ruff check .` | Clean |
| Types (engine) | `mypy engine/src/battle_engine` | Clean; source-file count 114 → **113** |
| Types (client) | `mypy client/src/battle_client` | Clean; 16 files |
| Modern agent execution | Fixed-seed `bytefray run` under Ruleset v2 and v4; byte-identical replay/result versus pre-removal | Unchanged |
| Tournament path | `bytefray tournament … --rounds 2` | **Still works** — proves the correct `--rounds` survived (§E.2) |
| CLI help | `bytefray run --help` | No `--mode`, `--red-a`, `--red-b`, `--core-size`, `--max-cycles`, `--max-processes`, `--max-len`, `--min-dist`, `--rounds` |
| Subcommand help | `bytefray --help` | "run a native Bytefray match" |
| Wheel | Build, then `python tools/check_wheel.py dist/bytefray-*.whl` | Passes with `ALLOWED_PMARS_PATHS` empty |
| Source distribution | `python -m build --sdist` | No `pmars` or `.red` members |
| Windows frozen build | `tools/build_win.ps1` | No `_internal/pmars/**` in any of the four trees |
| Windows installer | Inno Setup build (`%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe`) | Builds; payload roughly 337 KB smaller |
| Installed smoke | `tools/smoke_after_install.ps1` (edited) | Passes without the pMARS block |
| Replay/history regression | Replay History over a corpus **including a historical `redcode94` `result.json`** | Row present; `NOT_PRODUCED`; `N/A`; detail opens |

### S.2 Must prove — negative (the clean break)

This is what distinguishes "tests pass" from "V6 made a clean break." Each search
must return **only** the permitted survivors:

| Search | Permitted survivors |
| --- | --- |
| `git grep -i -E "pmars\|redcode" -- . ':!docs/archive/' ':!docs/research/' ':!docs/releases/' ':!CHANGELOG.md'` | Only §K.2 reader documentation plus §G.3/§G.4 reworded comments |
| `git ls-files '*.red'` | **Empty** |
| `git grep -n "PMARS_CMD"` | **Empty** outside archives |
| `git grep -n -- "--mode redcode94"` | **Empty** outside archives |
| `git ls-files pmars/ third_party_licenses/ warriors/ tools/pmars/` | **Empty** |
| `find dist -iname "*pmars*"` after a clean build | **Empty** |
| `bytefray run --mode redcode94 --red-a x --red-b y` | **Fails as an unrecognized argument** — never attempts execution |

The last row is the decisive user-facing proof: no current surface *claims or
attempts* Redcode execution.

### S.3 Changelog wording (§13 — brief suggestion only, not final prose)

Add a new V6 entry; **do not edit any prior release entry.** Something like:

> **Removed — Redcode/pMARS support.** Bytefray V6 is a Bytefray-agent platform
> and no longer executes Redcode warriors or invokes pMARS. `bytefray run`'s
> `--mode`, `--red-a`, `--red-b`, `--core-size`, `--max-cycles`,
> `--max-processes`, `--max-len`, `--min-dist`, and `--rounds` options are gone,
> Windows artifacts no longer bundle `pmars.exe`, and the `PMARS_CMD` environment
> variable is no longer read. Historical `redcode94` results remain **readable** —
> Replay History still lists them, reporting no replay and no applicable Ruleset —
> but are no longer reproducible. Releases up to and including v5.0.0 retain full
> Redcode support and remain available.

### S.4 Process constraints

Per the repository's standing qualification protocol: commit each batch **before**
the long suite runs, never overlap pytest invocations, give each its own
`--basetemp`, and verify HEAD and `git status` are unchanged across the run.

Note for this machine: **no elevated shell and no dedicated Linux host.** The
Linux frozen-build and installer-elevation checks must be delegated to CI
(`linux-package.yml`) or explicitly recorded as *not locally qualified*, rather
than reported at a stronger qualification tier than the evidence supports.

---

## T. Phase 3 architectural findings

Recorded, **not to be fixed during retirement**.

1. **`--mode` is a two-valued abstraction with one value left.** The
   `native`/`redcode94` selector exists only because two engines were unified
   behind one command. With Redcode gone, `cli.py`'s `run` path has a single
   execution model and the mode concept can leave the mental model entirely.

2. **`ResultEnvelope.backend` becomes a write-dead schema field.** One writer,
   zero semantic readers, retained only for historical decode. Phase 3 should
   decide whether it is documented as historical-only or kept as a genuine
   extension point.

3. **`SCHEMA_VERSION_V1` stops being a write target.** After retirement nothing
   emits a v1 result. The v1/v2 distinction collapses from "two live writers" to
   "one writer, one legacy read format", which may simplify `as_dict()`'s
   `if self.schema_version == SCHEMA_VERSION_V2` split at `result_model.py:183`.

4. **`termination_reason` has an out-of-enum value with no writer.**
   `"backend_completed"` was deliberately outside the native enum
   (`RESULT_SCHEMA.md:271-276`). Phase 3 can decide whether the enum tightens.

5. **`RulesetConfidence`'s `"not_applicable"` becomes purely historical.** With no
   non-Ruleset execution mode, every *new* artifact is `recorded`. The four-state
   vocabulary now describes an artifact's era rather than its kind.

6. **`ReplayState.NOT_PRODUCED` loses its only current producer.** Its docstring
   names pMARS as *the* intentional-absence case. After retirement the state is
   reachable only by historical rows — worth re-documenting, not removing.

7. **`cli.py` is a very large module with an early-return branch.** Removing 161
   lines from roughly 1,062 leaves a cleaner but still long
   parse-configure-dispatch function. Its natural seam — the mode branch —
   disappears, which may make extraction *easier* to reason about in Phase 3.

8. **Core War-era naming persists in live identifiers.** `SCHEMA_NAME =
   "battle2.result"`, `battle2.replay`, the `battle_engine`/`battle_client`
   package names, and the `arena`/`core` vocabulary. These are **retained
   compatibility identifiers** (`result_model.py:19-24` explains why) and are
   explicitly *not* retirement targets — but Phase 3's naming review should treat
   them as one deliberate cluster.

9. **The smoke harnesses hand-roll fixtures three times.** Phase 2B.4 found
   `warriors/`, `smoke_test.sh`'s heredocs, and `smoke_after_install.ps1`'s inline
   writes all reinventing the same warriors. Two of the three vanish with
   retirement; the residual duplication pattern in the smoke scripts deserves a
   Phase 3 look on its own terms.

10. **`tools/check_wheel.py`'s pMARS guard outlives its subject.** Keeping a
    negative assertion after the thing it guards against is gone is *good*
    defensive practice; Phase 3 should confirm it is documented as a permanent
    anti-regression check rather than left looking like residue.

---

## U. Risks and unresolved questions

### U.1 The one genuine open decision — `--mode`

Removing `--red-a`, `--red-b`, `--core-size` and the rest is unambiguous: they
are unreachable without `redcode94`. `--mode` is different, because
`--mode native` is *currently valid and harmless*.

| Option | For | Against |
| --- | --- | --- |
| **Remove `--mode` entirely** (recommended) | V6 is an explicit breaking retirement; a one-valued choice flag is noise; **zero in-repo callers pass `--mode native`** | A user script passing `--mode native` breaks with "unrecognized argument" |
| Keep `--mode` with `choices=["native"]` | Such scripts keep working | Preserves the retired concept in `--help`, contradicting §18's clean-break goal |
| Keep as a hidden deprecated no-op | Softest landing | Dormant configuration of exactly the kind §18 forbids |

**Recommendation: remove it entirely**, and name the removal explicitly in the
changelog (§S.3). Phase 2B.6 should confirm this before executing batch 3.

### U.2 Risks

| # | Risk | Likelihood | Mitigation |
| --- | --- | --- | --- |
| 1 | **Deleting the historical reader** (`result_model.py:287-288`) because it mentions `redcode94` | **Medium — the single most likely error in this phase** | §N.2's proof; the four `test_ruleset_persistence.py` tests must still pass. A count of 3,709 instead of 3,713 is the tripwire |
| 2 | **Removing the wrong `--rounds`** (`tournament_cli.py:45`) | Medium | §E.2; batch 3 verifies `bytefray tournament --rounds 2` |
| 3 | Deleting `pmars/` before editing the specs — the `os.path.isdir` guard then fails **silently**, producing a valid but quietly different build | Low | Batch ordering (5 after 4) |
| 4 | Over-scrubbing project lineage from `README.md`'s "Bytefray vs. Core War" table, `pyproject.toml:11`, or `PROJECT_HISTORY.md` | Medium | §K.3; §12 explicitly forbids it |
| 5 | Editing `CHANGELOG.md` or `docs/archive/**` history | Low | §13; batch 8 adds, never rewrites |
| 6 | Touching `_legacy/` "while we're in there" | Low | §L — **zero coupling**; it is out of scope entirely |
| 7 | Windows installer and frozen-build verification not reproducible locally (no elevated shell; Linux artifacts need CI) | **High on this machine** | Delegate to CI; record explicitly as not locally qualified rather than reporting a weaker tier as a stronger one |
| 8 | `ruff`/`mypy` unused-import residue after batch 3 (`hashlib`, `Path`, `stable_id`) | Medium | Batch 3 runs both; check whether each import has a surviving native use before deleting it |

### U.3 Unresolved questions for Phase 2B.6

1. **`--mode`** — §U.1. The only blocking decision.
2. **`"corewar"` in `pyproject.toml:16` keywords.** `"pmars"` is clearly a support
   claim and goes. `"corewar"` is arguably lineage (matching the description at
   `:11`) or arguably a discoverability claim. Recommend keeping it; flagged for
   the phase owner.
3. **`docs/RULES.md:484-492`** — delete the "Redcode/pMARS — not Ruleset v1"
   section, or retain a shortened historical note? It is currently load-bearing:
   `RULES.md:10,45,275,375`, `COMPATIBILITY.md:766`, `RESULT_SCHEMA.md:88`,
   `app/services/ruleset_options.py:120`, and `test_cli_agent_listing.py:58` all
   cite it. Recommend **retaining a short historical subsection** and repointing
   those references, rather than deleting it and orphaning seven citations.
4. **`test_cli_agent_listing.py:56-69`** asserts the agents legend **never
   mentions** Redcode/pMARS. This is a negative test that becomes *more* true
   after retirement — **keep it unchanged**; its docstring may be reworded.
5. **`docs/ROADMAP.md:108-116`** records a closed v0.10 decision that
   "Redcode/pMARS interoperability remains part of Bytefray's story."
   Recommend leaving the historical record intact and superseding it with the V6
   entry, rather than editing a closed roadmap item.

---

## Verification record

Performed after all investigation, immediately before this document was written
and again after writing it.

| Check | Result |
| --- | --- |
| `git status --porcelain` | Only `docs/research/v6/V6_PHASE2B5_REDCODE_PMARS_RETIREMENT_AUDIT.md` (untracked) |
| `git diff` | **Empty** — no tracked file modified |
| `git diff --check` | **Clean** — no whitespace errors |
| Source / test / CI / packaging / ruleset / `_legacy` files changed | **None** |
| `warriors/`, `pmars/`, `third_party_licenses/` modified | **No** — untouched, as §25 requires |
| CLI modes changed | **No** |
| `main` | `82549f9c3ccbdb2e13b8165b32afef00def4a8f2` — unchanged, matches `origin/main` |
| HEAD | `69035f790589f3651c27f660481800e10edd7c56` — unchanged |
| Temporary files staged | **None** — the §N.2 read-back script ran from the session scratchpad against a `tempfile.mkdtemp()` root |
| Commit / push performed | **No** — per §27, the report is left in the working tree for review |

**Investigative commands that wrote anything:** the §N.2 read-back script only,
which wrote into a system temporary directory outside the repository.
`git status --porcelain` was empty immediately after it ran.
