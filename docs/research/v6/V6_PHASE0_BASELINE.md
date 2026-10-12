# Bytefray V6 Research — Phase 0: Baseline Charter

**Status:** Phase 0 — Baseline establishment only. No gameplay, engine, or API
change is made in this phase.
**Starting branch:** `v6-research`, branched from `main` with zero divergence.
**Starting SHA:** `82549f9c3ccbdb2e13b8165b32afef00def4a8f2`
**Anchor release:** `v5.0.0` (tag `v5.0.0`); starting SHA is `v5.0.0` plus 10
documentation-only commits (release-publication record-keeping — no source
change). `git describe --tags` reports `v5.0.0-10-g82549f9`.

---

## 1. Purpose and scope

This phase does exactly one thing: establish a formally recorded, evidence-backed
starting point for V6 research, and freeze the released V5 state as immutable
historical evidence. It answers "what exists today, exactly, and what does the
next research program still not know" — nothing else. No mechanic, redesign, or
refactor happens in Phase 0.

V5 fixes may still happen on their own branch if something critical is found;
they are explicitly out of band from `v6-research` and must not leak into it.

---

## 2. Starting state

| Fact | Value |
|---|---|
| Branch created | `v6-research` |
| Branched from | `main` @ `82549f9c3ccbdb2e13b8165b32afef00def4a8f2` |
| Divergence at creation | none — `git rev-parse main` == `git rev-parse v6-research` |
| Working tree | clean (`git status --short` empty) at branch creation |
| Most recent tag reachable from HEAD | `v5.0.0` |
| Commits since `v5.0.0` | 10, all documentation-only (release-publication notes, README downloads section, Wayland support note) — verified both by commit subject (`git log v5.0.0..HEAD --oneline`) and by actual diff (`git diff --stat v5.0.0..HEAD`, excluding `docs/`, `CHANGELOG.md`, `README.md`, is empty); no `engine/`, `client/`, or `app/` source file changed |
| Remote tracking | `origin/main`, up to date |

---

## 3. Python / platform / toolchain baseline

- Interpreter in the active `.venv`: **Python 3.13.14** (win32, MSC v.1944 64-bit).
- Declared runtime support: **Python 3.10–3.14** (`pyproject.toml` `requires-python
  = ">=3.10"`, classifiers through 3.14). CI's `test-linux-core` matrix
  validates all five versions on Ubuntu; a separate, deliberately
  non-blocking `test-linux-core-next-python` job smoke-tests `3.15-dev` as
  early warning, outside the supported/tested matrix.
- Key installed dev-toolchain versions in `.venv`: `pytest==9.1.1`,
  `mypy==2.3.1`, `ruff==0.16.3`, `PyYAML==6.0.3`, `pygame-ce==2.5.8`,
  `PySide6==6.11.2`, `pyinstaller==6.22.2` (both canonical mypy invocations
  clean — see §4).
- pip 26.2.1, `.venv` at repo root (per `CLAUDE.md`; no second venv present).
- OS: Windows 11 Pro 10.0.26120. Windows is the primary GUI development
  target; Linux wheel is headless-first (`docs/LINUX_INSTALL.md`).
- Windows packaging toolchain: PyInstaller-based (`tools/build_win.ps1`,
  four `tools/*.spec` files), Inno Setup 6 installer (`tools/installer.iss`),
  AMD64 only.

---

## 4. Canonical test counts

Per `AGENTS.md`/`pytest.ini`, the canonical suite is `python -m pytest`
(`-m "not gui"` is baked into `addopts`), with `testpaths` = `_legacy/tests`,
`engine/tests`, `client/tests` — **not** `engine/tests` alone.

- **Collected (headless, excluding `gui`-marked):** 3,709 tests across 160
  test files (`_legacy/tests`: 1 file/2 tests; `engine/tests`: 159 files;
  `client/tests`: 17 files — some files split across both `client/tests` and
  `engine/tests` groupings above; exact per-file counts captured in the
  Phase 0 raw log).
- **Full-suite result (after the §4.1 environment repair, against a clean
  working tree):** **3,687 passed, 22 skipped, 0 failed, 0 errors** — 3,709
  total, exactly matching the collected count. Wall-clock: ~7 min 21 s
  (started 22:13:18, log last written 22:20:39, same local run). `HEAD`
  (`82549f9c3ccbdb2e13b8165b32afef00def4a8f2`) and `git status --short`
  (clean except the run's own gitignored `--basetemp` directory, removed
  afterward) were verified unchanged before and after.
- **mypy:** `mypy engine/src/battle_engine` → clean (114 source files).
  `mypy client/src/battle_client` → clean (16 source files).
- **ruff:** `ruff check .` → **all checks passed**, run against a working
  tree with no leftover pytest temp directory (see the note immediately
  below for why that precondition matters).

This is a discovery worth carrying forward: **do not run `ruff check .`
concurrently with, or immediately after, a still-running/just-finished
pytest invocation that used a non-standard `--basetemp`.** The standard
`.pytest-tmp/` is gitignored but not ruff-excluded either; delete it (or any
custom basetemp directory) before linting.

### 4.1 First run: 56 failures traced to a local, gitignored environment precondition gap — not a source defect

The **first** full-suite run against this exact commit produced 56 failed
(exact passed/skipped split not preserved — see note below — but
superseded by the clean re-run in any case). Every one of the 56 failures
traced to the identical root cause on inspection of tracebacks (`SystemExit: Unknown agent
'…'. Expected a folder …\agents\<name> with agent.yaml (JSON) or agent.py`,
`FileNotFoundError: …\agents\v4_claimer\agent.py`, `ValueError: could not
resolve an agent spec for 'v4_quorum'`, and downstream assertion failures in
tests that depend on those agents being resolvable):

The repo-root `agents/` directory (`.gitignore`'s "source checkouts use root
`agents/` as the writable runtime catalogue," entirely untracked) on this
machine had five of its `v4_*` starter-agent directories present but
**empty except for a stale `__pycache__`** (`v4_claimer`,
`v4_concentrated_attacker`, `v4_defender_scout`, `v4_local_defender`,
`v4_scout` — all five bundled V4 starters), and `v4_quorum` was **entirely
absent**. Every other catalog entry (V5 starters, dev-fixture agents, VM
binaries) was intact. This is local machine/checkout state, not anything
`git status` can see or `git` can restore — there is no tracked history for
this directory to diff against.

This was repaired using the repository's own documented, supported,
idempotent starter-installation function (`battle_engine.starters.
ensure_starter_agents`, called with `data_root` pointed explicitly at the
checkout root — a bare call resolves to `C:\ProgramData\Bytefray` on this
machine instead, because the `BYTEFRAY_ROOT` environment variable is set
here from an existing installed release; **the test suite itself
independently arranges for `D:\Projects\BATTLE2\agents` to be the target**,
which is how the failures reached the checkout path rather than
ProgramData). This is exactly the "non-destructively copies only missing
files" behavior `ARCHITECTURE.md` documents — the same repair an ordinary
`bytefray run`/`agents test` invocation performs automatically the first
time it needs an agent. It installed 31 previously-missing files (`agent.py`/
`agent.yaml`/one `README.md`) into six directories and modified nothing
git-tracked (`git status --short` before and after this repair is identical
except for the always-present, gitignored `.pytest-tmp*` directory). No
source file, test file, or fixture was edited to reach this fix.

**Repeated after repair:** a second full run against the identical, still-
unchanged commit produced **3,687 passed, 22 skipped, 0 failed** (~7 min
21 s) — the clean baseline reported above. A separate, unrelated
observation from both runs: pytest 9.1.1 did not write a final
`"N passed, M failed in Ws"` summary line to the redirected log in either
run (only the per-line `[NN%]` progress markers and, when applicable, the
`FAILED`-line short summary); the pass/fail/skip counts above were
recovered by counting `.`/`s`/`F` progress markers directly rather than
from a missing summary line. This is noted for anyone reproducing this
baseline who might otherwise assume the run was truncated.

**Disposition:** this is recorded as a **local-environment finding**, not a
V5/main source defect — nothing in `engine/`, `client/`, or `app/` was
touched to produce either the failure or the fix, and the repaired state
matches exactly what a fresh `bytefray run` on this checkout would have
produced on its own the first time it needed one of these agents. It is
recorded here in detail anyway, per this repository's evidence standard,
rather than silently re-run past.

---

## 5. Package / release state

- `pyproject.toml` version: `5.0.0`. `battle_engine.project_info.get_project_info()`
  confirms at runtime: `ProjectInfo(version='5.0.0', agent_api_version=2,
  result_schema_version=2, replay_schema_version=4, ...)`.
- Current GitHub Release: `v5.0.0` (published September 2026), with Windows
  installer, Python wheel, source distribution, and `SHA256SUMS` published.
- No open release-candidate or alpha branch for V6 exists yet; `v6-research`
  is the first V6 artifact.
- CHANGELOG's `[5.0.0]` entry confirms RC1 → final had no gameplay/Agent
  API/schema change — final release was hardening plus UX completion
  (process-share validation repair, Replay History, tournament UX,
  accessibility baseline, menu reorganization).

---

## 6. Current supported rulesets (verified against `battle_engine.rules`/`battle_engine.ruleset_policy` source, not docs alone)

`ruleset_policy._RULESET_POLICIES` registers exactly these 8 identities:

| Ruleset ID | Runtime | Agent API | Scheduler | Core placement | Process selection | Status |
|---|---|---|---|---|---|---|
| `bytefray-rules-1` | VM or Python | v1 | sequential | zero | priority | permanent, frozen (1.0) |
| `bytefray-rules-2` | Python only | v1 | sequential | seat_spread | priority | permanent, stable (2.0) |
| `bytefray-rules-2-alpha1` | any | any | sequential | zero | priority | historical alpha, frozen |
| `bytefray-rules-2-alpha11` | any | any | sequential | zero | priority | historical alpha, frozen |
| `bytefray-rules-3-alpha1` | Python only | v1 | sequential | seat_spread | priority | closed research-only identity; never exposed on any product CLI `--ruleset` choice; no stable Ruleset 3 exists |
| `bytefray-rules-4-alpha1` | Python only | v2 | chunked (Q=8) | seat_spread | priority | historical alpha, frozen, explicitly selectable |
| `bytefray-rules-4-alpha2` | Python only | v2 | chunked (Q=8) | seeded | round_robin | historical alpha, frozen, explicitly selectable |
| `bytefray-rules-4` | Python only | v2 | chunked (Q=8) | seeded | round_robin | **permanent, stable — current production default** |

- `OMITTED_RULESET_CANDIDATES = ('bytefray-rules-2', 'bytefray-rules-4',
  'bytefray-rules-1')` — the fail-closed resolution order for an omitted
  `--ruleset`, keyed off runtime kind / Agent API version of the roster.
- `PROCESS_RULESET_IDS` (the three multi-process v4 identities) =
  `{bytefray-rules-4-alpha1, bytefray-rules-4-alpha2, bytefray-rules-4}`.
- One historical alias: `evaluation-rules-1` → `bytefray-rules-1`
  (`rules._RULESET_ALIASES`), comparison-only, never rewrites stored
  artifacts.
- V5 shipped **no new Ruleset**; it built entirely on frozen `bytefray-rules-4`
  and Agent API v2 (agent authoring, parameterization, Designer/UX work only).

---

## 7. Repository metrics (git-tracked files only, `.venv`/`build`/`dist` excluded by virtue of not being tracked)

| Metric | Count |
|---|---|
| Total tracked files | 821 |
| Python files (`*.py`) | 430 |
| Total Python LOC (`wc -l`, all tracked `.py`) | 178,156 |
| — of which under `engine/src` | 47,807 (160 files) |
| — of which under `client/src` | 7,103 (17 files) |
| — of which under `app/` | 14,687 (35 files) |
| — of which under `_legacy/` (frozen fixture, excluded from lint) | 23 files |
| Test files (`test_*.py`) | 190 |
| Test LOC | 88,929 |
| — `engine/tests` | 63,467 (159 files) |
| — `client/tests` | 9,116 (17 files) |
| — `_legacy/tests` | 17 (1 file) |
| Markdown files | 206 |
| Files under `docs/` | 227 |
| Bundled/canonical agent examples (`engine/src/battle_engine/data/{starter_agents,reference_agents,v3_locality_agents,v3_closeout_agents,v3_phase7_agents}` + 4 `agent_template*` scaffolds) | 34 directories (18 starter, 4 reference, 6 v3-locality, 1 v3-closeout, 1 v3-phase7, 4 templates) |
| Additional tracked dev-fixture agents in the (otherwise gitignored) `/agents/` runtime root | 5 (`Nemesis`, `hydra`, `hydra_alpha2`, `nemesis_alpha2`, `viper`) |
| App package-local assets (`app/assets/`, `[tool.setuptools.package-data]`) | 1 tracked (`bytefray-icon.png`); branding logo lives at repo-root `assets/` referenced by README, not packaged |

Non-test Python source LOC ≈ 178,156 − 88,929 = **89,227**.

---

## 8. Major source directories and responsibility map

| Path | Responsibility |
|---|---|
| `engine/src/battle_engine/` (flat modules) | Simulation core: `config`, `instructions`, `agent_state`, `vm` (arena/ownership/decoding — standard-library-only, acyclic leaves) → `core` (compatibility re-export facade) → `match`/`scoring`/`statistics`/`results` → `telemetry` (replay/summary sink protocols) → `match_service.NativeMatchService` (canonical execution/orchestration boundary for every native match) → CLI/app layer. |
| `engine/src/battle_engine/builtins/` | Native VM bytecode assembly for `runner`/`writer`/`bomber`/`flooder`/`spiral`/`seeker`. |
| `engine/src/battle_engine/data/` | Package-local runtime data: starter/reference/template agents, v3 research-fixture agents, evaluation benchmark corpora (`data/benchmarks/*.json`). |
| `engine/src/battle_engine/evaluation_history/` | Qt-free discovery/comparison layer over `bytefray.evaluation` artifacts, including a `v2_adapter.py` (934 LOC) bridging older evaluation schema generations. |
| `engine/src/battle_engine/replay_history/` | Replay History subsystem backend (SQLite-cached discovery/index, `index.py` at 1,281 LOC) powering the Designer's History browser. |
| `engine/src/battle_engine/agent_evaluation.py` | Largest single module in the repo (5,467 LOC) — `agents evaluate` methodology across all four generations (v1/v2-pairwise/v2-group/v4-seeded). |
| `engine/src/battle_engine/process_runtime.py`, `python_runtime.py` | Production v4 multi-process model (fixed rosters, Q=8/round-robin scheduling, disruption) and Agent API v1/v2 Python execution respectively. |
| `client/src/battle_client/` | Replay-only consumer: `player`/`session`/`analysis`/`cli`, plus `renderers/` (`pygame_renderer.py` at 2,963 LOC, the largest client module; `pygame_canvas.py` is dead/unused code — see §10). Never re-executes an agent; never write-couples to the engine. |
| `app/` | PySide6 Agent Designer + Pygame-oriented desktop tools, packaged from repo root. `services/` (Qt-free business logic), `views/` (Qt widgets/dialogs), `widgets/` (reusable Qt controls), `assets/` (branding). Adjacent consumer of the engine, not part of `battle_engine.core`. |
| `_legacy/` | Frozen historical pre-v0.3 implementation (`core.py`, `agents.py`, `main.py`, `renderers.py`, `agents_tooling/`), retained as a *tested* migration/characterization fixture, excluded from lint, not shipped. |
| `docs/` | 227 tracked files: architecture/schema/compatibility references, `docs/specs/` (pre-implementation specs), `docs/research/{v4,v5}/` (open research), `docs/archive/{v1,v2,v3,v4}/` (closed-out historical records). |
| `tools/` | Windows build scripts, PyInstaller specs, Inno Setup installer script, wheel-content checker. |

---

## 9. Largest / highest-complexity modules

No cyclomatic-complexity tool (`radon`/`lizard`) is installed in this
environment; the table below uses line count as a size proxy only — it is
not a validated complexity metric, and should not be read as one without
running an actual complexity tool first if V6 work wants to act on it.

**Largest source modules (LOC):**

| File | LOC |
|---|---|
| `engine/src/battle_engine/agent_evaluation.py` | 5,467 |
| `client/src/battle_client/renderers/pygame_renderer.py` | 2,963 |
| `app/agent_designer.py` | 1,671 |
| `app/views/replay_history.py` | 1,669 |
| `engine/src/battle_engine/python_runtime.py` | 1,563 |
| `engine/src/battle_engine/match_service.py` | 1,533 |
| `app/views/evaluation_history.py` | 1,481 |
| `engine/src/battle_engine/agent_package.py` | 1,444 |
| `engine/src/battle_engine/spectator_derivation.py` | 1,396 |
| `engine/src/battle_engine/process_runtime.py` | 1,367 |
| `engine/src/battle_engine/replay_history/index.py` | 1,281 |
| `app/services/replay_history_presentation.py` | 1,192 |
| `engine/src/battle_engine/spectator_perspective.py` | 1,183 |
| `engine/src/battle_engine/agent_test.py` | 1,134 |
| `engine/src/battle_engine/cli.py` | 1,062 |

**Largest test modules (LOC — a proxy for how heavily-characterized a
subsystem is, not for source complexity):**

| File | LOC |
|---|---|
| `client/tests/test_pygame_renderer.py` | 2,568 |
| `engine/tests/test_replay_history.py` | 1,646 |
| `engine/tests/test_agent_package.py` | 1,569 |
| `engine/tests/test_agent_evaluation_v2.py` | 1,529 |
| `engine/tests/test_v4_spectator_derivation.py` | 1,352 |
| `engine/tests/test_evaluation_history.py` | 1,310 |

`agent_evaluation.py` at 5,467 LOC is nearly double the next-largest module
and is a natural first candidate for a future "measure before splitting"
pass — but per the Phase 0 charter's non-goals (§13), no such split happens
in this phase.

---

## 10. Known duplicated / legacy systems

- **`_legacy/`** — frozen pre-v0.3 implementation, deliberately retained as
  a tested migration fixture (`_legacy/tests/test_smoke.py`), excluded from
  ruff, included in `pytest.ini` `testpaths`. Not a duplication risk in
  practice (nothing imports it from the active tree) but adds to file/LOC
  totals in any repo-wide scan.
- **`client/src/battle_client/renderers/pygame_canvas.py` (`PygameCanvas`)**
  — explicitly documented in `ARCHITECTURE.md` as **unused, unremoved
  code**: no caller anywhere in the repository, not wired into the
  Designer. A concrete, evidence-backed deletion candidate for a future
  "delete before refactoring" pass — not acted on in Phase 0.
- **`ARCHITECTURE.md`'s own header is stale**: it self-describes as
  covering "through v4.0.0-alpha1" and enumerates milestones only up to
  v0.7, despite the repository being at v5.0.0 with a v4-stable Ruleset,
  V5 Replay History, tournament UX, and accessibility work all shipped
  since. The document's *body* (read in full for this baseline) is still
  substantially accurate for the engine/client boundary, but the framing
  header and its milestone-delivery-history closing sections have not been
  updated across v4.0.0-rc1 through v5.0.0. This is a documentation-hygiene
  finding, not a code duplication — flagged here because a V6 phase reading
  only the header could draw a stale conclusion.
- **Three v4 Ruleset identities sharing one implementation** —
  `bytefray-rules-4`, `-alpha1`, `-alpha2` are *not* duplicated
  implementations; `RULES_V4.md`/`COMPATIBILITY.md` and
  `engine/tests/test_v4_stable_ruleset_equivalence.py` establish this is
  one semantic implementation gated on `RulesetPolicy` field values,
  exposed under multiple compatibility identities. Recorded here explicitly
  so a future V6 phase doesn't mistake this deliberate multi-identity
  design for something to "clean up."
- **Evaluation schema/identity generations** — five additive
  identity/schema versions exist for `bytefray.evaluation` (v1 historical
  through v4-seeded, versions 4–7 plus the original v1), each with its own
  adapter/compatibility code (`evaluation_history/v2_adapter.py` and
  related). This is deliberate historical-artifact honesty per
  `docs/COMPATIBILITY.md`, not accidental duplication — but it is real,
  substantial compatibility-surface weight a future measurement pass should
  be aware of before proposing to "simplify" evaluation code.
- **No second/parallel gameplay implementation was found** for placement,
  scheduling, or termination — `docs/RULES_V4.md`/`ARCHITECTURE.md` state
  this as a design invariant (one production seam for placement, one for
  scheduling), and nothing found during this baseline pass contradicts it.

---

## 11. Current gameplay assumptions (as of `bytefray-rules-4`, the stable production Ruleset)

- **Spatial multi-process model.** Each entrant declares a fixed roster of
  one or more processes before tick 0, each with its own arena anchor and
  circular reach. `READ`/`WRITE` act only within a process's own reach;
  `MOVE` relocates a process's anchor.
- **Shared per-entrant action budget.** `Q = 8` actions/tick, split across
  an entrant's own processes by declared `share` (largest-remainder
  rounding), handed out to eligible processes **in rotation** (not
  declared-list priority).
- **Disruption.** A live enemy `WRITE` landing exactly on a process's
  anchor disrupts it for the remainder of that tick; its share is
  redistributed among the entrant's other eligible processes.
- **Seeded core placement**, not a fixed evenly-spread layout: entrant
  cores are derived from the match seed subject to a minimum 64-cell
  circular separation. `enemy_core_base = own_core_base + arena_size // 2`
  is **not** a valid assumption under this Ruleset (it was valid only under
  `bytefray-rules-4-alpha1`'s fixed seat layout).
- **Victory conditions**, unchanged since Ruleset v1/v2: core capture
  (owning 0 of an entrant's core cells eliminates it; the entrant that made
  the final overwrite gets kill credit), last-agent-standing outright win
  (scores not consulted), tick-limit fallback to highest score among
  survivors, tie on equal survivor scores or zero survivors.
- **Deterministic RNG** — independent per-agent PRNG streams derived from
  the match seed; identical `(seed, arena_size, entrant_count, agents)`
  reproduces identical matches.
- **Agent API v2** (`reset`/`declare_processes`/`act`) is the stable,
  documented 4.x/5.x Python programming contract; Agent API v1 remains
  frozen and supported only for Ruleset v1/v2.
- **Scoring formula, arena mechanics (ownership/last-writer), and winner
  resolution are unchanged** from Ruleset v1/v2's shared foundation — V4's
  entire gameplay delta is the process/spatial layer described above; V5
  changed no gameplay at all (see §5).
- **No fog-of-war / partial observability**, no replication, no mutation,
  no explicit `ATTACK`/`DEFEND` action — all offense/defense remain
  emergent from `READ`/`WRITE`/ownership plus the v4 process primitives.

---

## 12. Explicit V6 research questions

Framed from what `docs/FUTURE_PLANS.md` still lists as open **Research**
(not Candidate) after the v2.0-alpha, v3, and v4-pre-RC programs closed,
narrowed to what is actually unresolved rather than restating settled
ground:

1. **Is there any evidence-backed need for a gameplay change at all right
   now**, or does V6 close as a pure measurement/hygiene program the way
   the v3 program closed without creating a stable Ruleset 3? (The
   charter's own guiding rule in §14 says this should be treated as the
   default null hypothesis, not an assumption a mechanic is needed.)
2. **Multiple execution processes belonging to a single entrant** —
   explicitly distinct from the already-validated v4 "one entrant declares
   several processes" model — remains untested: could a *single* logical
   controller directing several independently-acting entrant-components
   (beyond v4's shared-anchor-roster model) produce meaningfully different
   strategic behavior, and is there any real evidence it's needed?
3. **Replication / deployment economics** — spawning or deploying
   additional execution centers mid-match — has never been prototyped or
   validated in any prior program. Is there a minimal, hypothesis-driven
   experiment that could characterize whether this creates real strategic
   choice rather than a free multiplier, before any design work begins?
4. **Agent lifecycle: mutation and evolution** (offline between-match vs.
   online during-match, and what a meaningful "cost" would be) — a
   `docs/FUTURE_PLANS.md` cluster of candidates with zero prior
   experimentation. Does V6 need to touch this at all, or is it still
   correctly deferred?
5. **Execution-trace / intent semantics** — the v3 closeout's own named
   "most promising unaddressed direction" if defense's scoring deficit is
   ever revisited: could new observable execution telemetry (e.g. "was this
   `WRITE` preceded by damage-revealing `READ`") distinguish responsive
   defense from blind rewriting, where ownership-history-based designs
   (v3 Phase 5A/6) provably could not? This would need its own anti-gaming
   analysis before being worth prototyping.
6. **Information density / fog-of-war** — named in `docs/FUTURE_PLANS.md`
   as untested by any program. Is partial observability worth a
   hypothesis-driven pilot, and if so, what would the minimal falsifiable
   experiment look like?
7. **Evaluation/ranking systems** (Elo/Glicko/TrueSkill-style) remain
   explicitly not built and not a V6 requirement by default — is there
   concrete evidence (usage, support burden, a real comparative-ranking
   need) that would justify reopening this, given `docs/FUTURE_PLANS.md`'s
   standing caution against building it speculatively?
8. **Repository/architecture measurement**, independent of any gameplay
   question: does `agent_evaluation.py`'s 5,467-LOC size (§9), the
   evaluation-schema generation count (§10), or any other measured hotspot
   in this baseline actually cause a real, evidenced problem (support
   burden, defect rate, onboarding friction) worth a "delete before
   refactor" pass — or is it simply large and otherwise healthy (clean
   mypy, passing golden-equivalence corpus, no duplicated implementation
   found)?
9. **Is `ARCHITECTURE.md`'s stale framing header (§10) worth a documentation
   correction pass on its own**, separate from any gameplay research, so a
   future session doesn't inherit a wrong mental model of what shipped
   since v0.7?

None of the above is pre-answered by this phase. Phase 0 states the
questions; it does not gate, design, or prototype answers to any of them.

---

## 13. Charter non-goals for V6

- **No new gameplay mechanics** until a specific research question above
  (or one discovered later, following the same discipline) produces actual
  evidence a mechanic is needed. No mechanic is designed, prototyped, or
  implemented "because it seems like it would be useful."
- **No broad GUI redesign.** Designer/Replay Viewer changes, if any, follow
  evidence of a real gap the way v1.1/v1.3/V5 Alpha 1 did — not a
  refresh for its own sake.
- **No speculative rewrites.** Nothing in `engine/`, `client/`, or `app/` is
  restructured on the belief that a cleaner shape "might be needed
  someday."
- **No "we might need this someday" compatibility preservation without
  evidence.** A compatibility surface is kept because something currently
  depends on it (checked, not assumed) — not proactively added for a
  hypothetical future consumer.
- **No architectural churn merely to make files smaller.**
  `agent_evaluation.py`'s size (§9) is recorded as a fact, not treated as
  an automatic mandate to split it.

## 14. Guiding rule

> **Delete before refactoring; refactor before redesigning; measure before
> changing gameplay.**

Every subsequent V6 phase should be able to point to which of these four
verbs it is doing, and to the measurement or evidence that justified it.

---

## Appendix: reproduction commands

```
git rev-parse HEAD                       # 82549f9c3ccbdb2e13b8165b32afef00def4a8f2
git status --short                       # (clean)
git describe --tags --always             # v5.0.0-10-g82549f9
git log v5.0.0..HEAD --oneline           # 10 doc-only commits
git diff --stat v5.0.0..HEAD -- . ':!docs' ':!CHANGELOG.md' ':!README.md'  # (empty)

# One-time local repair (gitignored agents/ catalog only, see §4.1):
python -c "from pathlib import Path; from battle_engine import starters; \
print(starters.ensure_starter_agents(data_root=Path('.')))"

python -m pytest -q --basetemp=.pytest-tmp-phase0b
# 3,709 collected -> 3,687 passed, 22 skipped, 0 failed, 0 errors (~7m21s)
mypy engine/src/battle_engine            # clean, 114 files
mypy client/src/battle_client            # clean, 16 files
ruff check .                             # All checks passed! (clean working tree, no leftover basetemp dir)
python -c "from battle_engine import project_info; print(project_info.get_project_info())"
python -c "from battle_engine import ruleset_policy; print(sorted(ruleset_policy._RULESET_POLICIES))"
```
