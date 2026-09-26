# Bytefray V5 Alpha 1 Maintenance — Phase 0: Baseline Lock

**Status:** Baseline established. No cleanup performed in this phase.
**Discipline:** Read-only investigation and documentation only. No production,
test, packaging, gameplay, agent, or replay file was modified. This report is
the only file this phase adds.

---

## A. Baseline

### Repository identity

| Item | Value |
|---|---|
| Branch | `v5-research` |
| HEAD SHA | `198a94ed70bc9e1ae8a26a13fe33094377712b63` |
| Upstream/tracking branch | `origin/v5-research` |
| Ahead/behind upstream | `0` / `0` (exactly up to date) |
| Working-tree state (start and end) | Clean — `nothing to commit, working tree clean` |
| Product version (`pyproject.toml`) | `5.0.0a1` |
| Relationship to `main` | `main` @ `4ad09f2` (`docs: finalize README for Bytefray v4.0.0`) is an ancestor of `v5-research`; `v5-research` is 31 commits ahead of `main`, `main` has 0 commits `v5-research` lacks |

### Alpha 1 identification — important distinction

**The current checkout (`198a94e`) is NOT byte-identical to the publicly
published Alpha 1 release.** This must be understood before any later phase
reasons about "what Alpha 1 users are seeing."

- The published release is tag `b5.0.0-alpha1` → commit
  `28a10b8f8fd47bf32ec9281dcc21b0645276962c`, published as a GitHub prerelease
  on 2026-09-10 (see `docs/research/v5/V5_ALPHA1_PHASE_F_FINAL_QUALIFICATION.md`,
  "Publication addendum"). That commit is what the seven uploaded release
  assets (wheel, sdist, four frozen executables, installer) were built from,
  and it is what Alpha 1 feedback is actually being gathered against.
- Current HEAD is **10 commits ahead** of that tag:

  ```
  28a10b8  (published b5.0.0-alpha1)
  a224469  docs(v5): record alpha1 publication qualification
  0f679f7  docs(v5): publish alpha1 release documentation
  77b6856  docs(v5): record post-release hardening audit
  e67787e  fix(v5): restore parameter consistency across execution paths   <- behavioral
  75f5a2d  chore(v5): clean repository and release surface
  ec89438  docs(v5): clarify historical documentation boundaries
  11d2be0  README updates for version 5. Might be too verbose or dense
  0d94d6a  feat(v5): improve core capture presentation                    <- behavioral (client-side)
  0b414a2  docs(v5): add visual project showcase
  198a94e  docs(readme): surface Agent Designer earlier                   <- HEAD
  ```

- Two of these ten commits are **not** documentation/chore-only:
  - **`e67787e` ("fix(v5): restore parameter consistency across execution
    paths")** changes real engine behavior: `agent_evaluation.py`,
    `agent_parameters.py`, `agent_test.py`, `supervised_runtime.py`,
    `tournament_cli.py`, and `tournament_service.py`. It is the remediation
    of FIND-01/FIND-02 from
    `V5_ALPHA1_POST_RELEASE_HARDENING_AUDIT.md`, fully recorded in
    `V5_POST_RELEASE_H1_PARAMETER_CONSISTENCY.md`. Before this commit,
    `bytefray tournament`, `agents test`, and `agents evaluate` silently
    resolved Agent API v2 schema parameters to `{}` instead of their declared
    defaults; after it, they resolve identically to `bytefray run`. This is a
    genuine, intentional, already-landed gameplay-adjacent behavior change
    made *after* the Alpha 1 tag was published.
  - **`0d94d6a` ("feat(v5): improve core capture presentation")** changes
    `client/src/battle_client/player.py` and
    `client/src/battle_client/renderers/pygame_renderer.py`. Inspection of the
    diff (see Section C) shows this is confined to `PlaybackController`
    movement-kind bookkeeping and Pygame Replay Viewer visual-effect
    rendering (core-destruction/capture callout animation). It does not
    touch `engine/src`, replay schema, or tick advancement logic — it is
    presentation-only, but it is still a change to a nominally protected
    surface (Replay Viewer rendering) made after publication.

- **This report does not undo, flag as a defect, or recommend reverting
  either commit** — both were deliberate, already-qualified, user-authored
  changes that predate this Phase 0 task's existence, not violations of an
  invariant that didn't exist yet. They are recorded here because Phase 0's
  job is to establish an honest reference point, and "HEAD equals the
  published artifact" would be false.
- **Recommendation, left to the user to confirm:** treat **current HEAD
  (`198a94e`)**, not the older tag, as the baseline that Phases 1–3's
  "must not change behavior" invariants apply *going forward* from. The
  published tag remains the historical record of exactly what Alpha 1
  testers downloaded; current HEAD is the practical maintenance baseline.
  If the user instead wants strict behavioral identity with the exact
  published artifact, `e67787e` and `0d94d6a`'s effects would need explicit
  separate review — this report takes no position beyond flagging the
  choice.

### Ruleset identifiers currently exposed

No Ruleset v5 exists. V5 is an agent-authoring/parameter/Designer/UX
generation built on **unchanged V4 gameplay**. The five Ruleset identities
selectable across all three CLIs (`bytefray run`, `bytefray tournament`,
`agents test`/`evaluate`) are, verified directly from each parser's
`choices=[...]`:

- `bytefray-rules-1` (frozen, Agent API v1 only)
- `bytefray-rules-2` (frozen, Agent API v1 only; API-v1's omitted-ruleset
  default)
- `bytefray-rules-4-alpha1` (frozen alpha, Agent API v2)
- `bytefray-rules-4-alpha2` (frozen alpha, Agent API v2)
- `bytefray-rules-4` (permanent stable identity, gameplay-identical to
  alpha2; Agent API v2's omitted-ruleset default)

Verified live: `bytefray --version` reports
`Bytefray 5.0.0a1, Agent API v2, result schema v1, replay schema v4, Python 3.13.14`.

---

## B. Environment

| Item | Value |
|---|---|
| Host OS | Windows 11 Pro, build `10.0.26120` |
| Shell | PowerShell 7 (primary), Git Bash also available |
| Development interpreter | CPython `3.13.14` (`.venv/Scripts/python.exe`) |
| `bytefray` install mode | editable (`pip install -e .`), resolves to `D:\Projects\BATTLE2\engine\src\battle_engine\__init__.py` |
| Repo-level `.python-version` | **Does not exist anywhere in the repository** (`Glob **/.python-version` found zero matches) — nothing to be inconsistent with |
| `pyproject.toml` | `requires-python = ">=3.10"`; classifiers list `3.10`–`3.14` |
| CI (`.github/workflows/ci.yml`) | Core matrix `['3.10', '3.11', '3.12', '3.13', '3.14']`; a separate informational, non-blocking job tracks `3.15-dev` |
| `AGENTS.md` | States "Runtime Python support is 3.10 through 3.14; CI validates all five. Some legacy *release-build* tooling pins Python 3.11 for reproducible PyInstaller executables — that does not raise the package's runtime minimum." |

**Finding: no Python-version inconsistency exists.** All four sources
(`pyproject.toml`, CI, `AGENTS.md`, and the absence of any `.python-version`
file) agree on 3.10–3.14 runtime support, with 3.11 pinned only for release
*build* tooling reproducibility, not the runtime floor. The originally-listed
candidate ".python-version inconsistencies" is not present in this
repository as of this baseline; there is no file to reconcile.

---

## C. Test baseline

All commands run from `D:\Projects\BATTLE2` using `.venv\Scripts\python.exe`
against the exact HEAD above. No production code was changed to make any of
these pass — all passed as found.

| Command | Result |
|---|---|
| `python -m pytest` (full headless suite, `pytest.ini`'s default `-m "not gui"`) | **3395 passed, 21 skipped, 3 deselected** in `341.81s` |
| `python -m pytest engine/tests -k "v5 or ruleset"` (focused V5/ruleset subset) | **731 passed, 0 skipped, 0 failed, 0 errors** in `45.97s` |
| `mypy engine/src/battle_engine` | `Success: no issues found in 107 source files` |
| `mypy client/src/battle_client` | `Success: no issues found in 16 source files` |
| `ruff check .` | `All checks passed!` |
| `bytefray --version` (packaging/import/version smoke) | exit `0`; `Bytefray 5.0.0a1, Agent API v2, result schema v1, replay schema v4, Python 3.13.14` |

No failures were observed at any gate. No flakes were observed (each command
was run once; the counts match the most recent prior qualification record in
`V5_POST_RELEASE_H1_PARAMETER_CONSISTENCY.md` almost exactly — that report's
full run showed `3395 passed, 0 failed, 0 errors, 23 skipped`, a difference
of 2 skips from this run's 21, most plausibly explained by environment-gated
skips such as `BYTEFRAY_FROZEN_EXE`-dependent tests whose skip/collect count
can shift with whether a frozen executable happens to be present in
`dist/windows` at collection time — not investigated further, as it does not
affect the failure count and is explicitly out of this phase's remit to
repair or explain exhaustively).

This checkout is a genuinely trustworthy baseline: full suite, focused
suite, both mypy invocations, and lint are all simultaneously clean.

---

## D. Protected Alpha 1 behavior surface

| Subsystem | Reason protected | Maintenance risk level |
|---|---|---|
| Ruleset gameplay semantics (`bytefray-rules-1/2/4/4-alpha1/4-alpha2`) | Directly what Alpha 1 players are experiencing and giving feedback on; any change invalidates match-result comparisons across the feedback window | **PROHIBITED DURING FEEDBACK** |
| Scheduler/process behavior (`scheduler.py`, `process_runtime.py`, `supervised_runtime.py`) | Determines tick order and multi-process execution; any change is a gameplay change | **PROHIBITED DURING FEEDBACK** |
| Observation/action APIs (Agent API v1 `MatchContext`, Agent API v2 `MatchContextV2`/`ActionKindV2`) | Changing shapes or semantics breaks agents Alpha 1 users have already authored | **PROHIBITED DURING FEEDBACK** |
| Deployment/replication, mortality, territory/core mechanics | Core gameplay mechanics under active user evaluation | **PROHIBITED DURING FEEDBACK** |
| Scoring (`scoring.py`, `ScoringPolicy`) | Directly affects match outcomes and evaluation comparisons | **PROHIBITED DURING FEEDBACK** |
| Victory/termination logic (`RulesetPolicy.resolve_termination`) | Same as above | **PROHIBITED DURING FEEDBACK** |
| Seeding/randomness, determinism (seed-derived core placement, deterministic replay reproduction) | Alpha 1's determinism guarantee (same seed+agents+config -> same result) is a headline qualified property; breaking it invalidates every existing bug report tied to a seed | **PROHIBITED DURING FEEDBACK** |
| Agent API contracts (v1 and v2), agent loading, parameter handling, presets, validation | Users are actively authoring agents against these contracts today | **PROHIBITED DURING FEEDBACK** |
| Starter/reference agents (`v5_core_defender`, `v5_dual_team`, `v5_region_attacker`, `v5_scout_striker`, six `v4_*` agents, historical `v1`/`v2`-era starters) | Users' first experience and reference material; changing shipped starter behavior is a silent gameplay change | **PROHIBITED DURING FEEDBACK** (starter *packaging hygiene* — e.g. FIND-03/04 below — is a narrower, still-deferred exception; see Section E) |
| CLI match creation (`bytefray run`, `bytefray tournament`, `agents test`/`evaluate`) | User-facing workflow surface already in use | **REQUIRES SPECIAL REVIEW** — flag/help-text/error-message wording can usually change safely; argument semantics, defaults, and ruleset/parameter resolution cannot |
| GUI/Designer match creation, Ruleset selection, entrant selection, seed handling, Randomize Seed | Same as CLI, plus the Designer is the primary Alpha 1 onboarding path | **REQUIRES SPECIAL REVIEW** |
| Replay generation | Determines what gets recorded in every match a user runs during the feedback window | **PROHIBITED DURING FEEDBACK** |
| Replay schema/serialization (schema v4) | Existing Alpha 1 replay files must stay readable | **PROHIBITED DURING FEEDBACK** |
| Replay loading, playback semantics (tick advancement, `PlaybackController` navigation) | Same as above; note `0d94d6a` already touched `PlaybackController` post-publication (Section A) without altering tick semantics — any *further* touch here needs the same scrutiny | **REQUIRES SPECIAL REVIEW** |
| Replay Viewer *rendering*/visual presentation only (no semantic/data change) | Presentation-only changes (as `0d94d6a` demonstrated) are lower risk than schema/semantic changes, but still user-visible | **SAFE IF DEMONSTRABLY BEHAVIOR-NEUTRAL** — "behavior-neutral" here means provably no change to recorded replay content, tick advancement, or any value a user could rely on, verified by the existing renderer/playback test suite plus manual review |
| Designer workflows currently exposed to Alpha 1 users (Battle/Replay/Analyze navigation, Simple/Advanced match setup, entrant cards) | User-visible defaults and flows already documented/screenshotted for Alpha 1 | **REQUIRES SPECIAL REVIEW** — cosmetic/wording changes are lower risk; reordering or removing an exposed workflow step is not |
| User-visible defaults anywhere (scoring weights, arena size, tick limits, omitted-ruleset resolution, omitted-parameter resolution) | Changing an unstated default is functionally a silent gameplay change | **PROHIBITED DURING FEEDBACK** |

Everything in this table is explicitly **out of scope for Phase 1–3 cleanup**
unless a later phase can demonstrate, with test evidence, that a specific
change is behavior-neutral (invariant 11, Section G).

---

## E. Cleanup inventory

Evidence-backed candidates found by direct repository inspection, plus the
prompt's suggested list resolved against what actually exists today.

| Candidate | Location | Evidence | Classification | Risk | Recommended phase |
|---|---|---|---|---|---|
| Stale `SECURITY.md` "Supported release line" section | `SECURITY.md:5-13` | States the current line is "the `4.x` prerelease series, currently `4.0.0-rc1`" and "the most recent stable release remains `3.0.0`". Both are false today: `4.0.0` shipped stable on 2026-09-08 (`CHANGELOG.md`), and `5.0.0a1` is the current published prerelease (Section A). Also calls Ruleset `bytefray-rules-4-alpha1` "the" Agent-API-v2 ruleset, ignoring the now-permanent `bytefray-rules-4`. | **A** | Low — prose only, no executable path | Phase 1 |
| CLI `--pygame` flag | `engine/src/battle_engine/cli.py:304-308` | `help="(deprecated/no-op) rendering moved to \`bytefray replay\`"` — the flag is parsed (`action="store_true"`) but its value is never read elsewhere in `cli.py` (not verified exhaustively for every possible reference; see Section F) | **C** (the flag's *effect* is provably already inert) / **D** (removing the argument itself changes what `bytefray run --pygame ...` does — from silently accepted to a parse error) | Recommend leaving the flag accepted (no removal) and only tightening its help text (A) unless a later phase explicitly wants to close the compatibility surface, which is a D-level product decision | Phase 1 (docs only) / Phase-D-deferred (removal) |
| Installer creates a `replays` and a `logs` data-root subdirectory that no runtime code ever writes to | `tools/installer.iss:52,54` (`Name: "{code:GetDataRoot}\replays"`, `\logs`); cross-checked against `engine/src/battle_engine/paths.py`'s `canonical_replay_directory`, which only ever looks under `root/runs/_designer`, `root/runs/_loose`, and `root/runs` — never a top-level `replays/`; a repo-wide search for the literal strings `"replays"`/`"logs"` found no writer, only `tools/installer.iss`'s directory-creation lines and `tools/smoke_after_install.ps1:153`'s writability check of the same four installer-created directories | **C** (installer-only; creates an always-empty directory on every install, verified by a dedicated smoke check rather than any real writer) | Low-moderate — release/installer tooling, needs an installer-lifecycle smoke re-run, not just a unit test | Phase 3 (release-surface cleanup) |
| `docs/research/v5/V5_ALPHA1_POST_RELEASE_HARDENING_AUDIT.md` FIND-03 — non-atomic `_mirror_bundled` starter refresh | `engine/src/battle_engine/starters.py:390-414` | Re-verified present at current HEAD: files are still written sequentially in place with no staging directory/atomic rename | **C** | Moderate — touches the starter-refresh path that runs on every product launch; needs interruption-simulation regression coverage before any fix | Phase 2 |
| Same audit, FIND-04 — `starter_content_files` only excludes `__pycache__` by exact-case directory name, not loose `.pyc`/`.pyo` files or case variants | `engine/src/battle_engine/starters.py:153-164` | Re-verified present: `if "__pycache__" in candidate.parts:` with no suffix filter | **C** | Low | Phase 2 |
| Same audit, FIND-05 — `tools/build_linux.sh` has no post-build bytecode/debris guard (unlike `tools/build_win.ps1`) | `tools/build_linux.sh` | Re-verified: no `.pyc`/`__pycache__` check found in the script | **C** | Low — Linux PyInstaller binaries are not currently CI-gated or released, so today's exposure is latent | Phase 3 |
| Same audit, FIND-06 — `agent_designer.spec`/`replay_viewer.spec` bundle the entire repo-root `assets/` (including a 1.16MB marketing brand sheet) instead of just `app/assets/branding` like `bytefray.spec` does | `tools/agent_designer.spec:12,46`; `tools/replay_viewer.spec:11,24`; contrast `tools/bytefray.spec:12,74` | Re-verified present at current HEAD — both specs still use `assets_dir = os.path.join(project_root, "assets")` and `collect_data_tree(assets_dir, "assets")` | **C** | Low — binary bloat only, no behavior change | Phase 3 |
| Same audit, FIND-07 — `packaging_data.py`'s cache-directory check is case-sensitive | `tools/packaging_data.py:82` (`if any(part == CACHE_DIRECTORY_NAME for part in path.parts):`) | Re-verified present | **C** (informational-severity per the audit) | Very low | Phase 3 |
| Repo-root `agents/` directory contains agents never bundled as V4/V5 starters | `agents/` (top level) vs. `engine/src/battle_engine/data/starter_agents/` | `agents/` has `Nemesis`, `bomber`, `chatgpt_hunter`, `claude_agent`, `hydra`, `hydra_alpha2`, `nemesis_alpha2`, `replicator`, `viper` in addition to the current starter set; `starter_agents/` (the packaged set) has exactly the six `v4_*`, four `v5_*`, and the historical `adaptive`/`claimer`/`hunter`/`raider`/`runner`/`seeker`/`sentinel`/`spiral`/`strider`/`wanderer`/`writer` agents. Per `AGENTS.md`, repo-level `agents/` is runtime/user data, not package data, so this is not a packaging leak — but several of the extra names look like development/research fixtures (e.g. `hydra_alpha2`, `nemesis_alpha2` read as leftover alpha-research artifacts) | **B** (must be proven unused — not yet checked for doc/test references) | Not yet assessed — needs Section 5-style reference analysis before any classification of individual agents | Phase 1 (inventory/reference-check only) |
| `sync_ruleset_choices` (old name, prompt's named candidate) | — | **Already resolved, not a live candidate.** The function was already renamed to `sync_ruleset_choices_for_metadata` (`app/widgets/ruleset_combo.py:44`, called from `app/views/development.py` and `app/views/evaluation.py`), and a regression test already exists asserting the old name is gone: `tests/test_v5_alpha1_phase_e_designer_ux.py:747-754` (`assert not hasattr(module, "sync_ruleset_choices")`). No action needed. | N/A | N/A | Not applicable |
| `release_notes.txt` (prompt's named candidate) | — | **Does not exist anywhere in the repository** (`find -iname "release_notes*.txt"` returned nothing). Release notes live in `CHANGELOG.md` and per-release GitHub prerelease bodies. No action needed. | N/A | N/A | Not applicable |
| `.python-version` inconsistencies (prompt's named candidate) | — | **No such file exists at all** (Section B). Nothing to reconcile. No action needed. | N/A | N/A | Not applicable |
| `docs/ROADMAP.md` "Current V5 boundary" section | `docs/ROADMAP.md:28-39` | Already correctly states V5 is current and `5.0.0a1` is published; not stale. Checked because the prompt flagged "obsolete V4/V5 comments or roadmap language" as a candidate category — this specific document does not qualify. | N/A | N/A | Not applicable (no change needed) |
| `EngineRunner` (prompt's named candidate, "obsolete/dead EngineRunner material") | `app/services/engine.py` | Live, in-use service class (referenced by `engine/tests/test_designer_third_entrant_command.py`, `engine/tests/test_pmars.py`). No dead/superseded `EngineRunner` implementation was found elsewhere in the tracked tree. **Not a live cleanup candidate as currently understood** — flagged for a closer pass in Phase 1 in case a narrower obsolete code path inside it exists that this grep-level pass did not surface. | — | — | Phase 1 (verify only) |

**Classification totals:** A = 1 (`SECURITY.md`); B = 1 (repo-root `agents/`
extras, unresolved pending reference analysis); C = 7 (`--pygame` help text
is really A, counted once above; installer dead dirs; FIND-03/04/05/06/07);
D = 0 confirmed (the `--pygame` *removal* question is the only D-adjacent
item, and this report recommends not removing it during the feedback
window regardless). No Category D change is proposed by this inventory.

---

## F. Hidden-coupling findings

- **`sync_ruleset_choices_for_metadata` is genuinely load-bearing**, called
  from both `app/views/development.py:795` and `app/views/evaluation.py:323`
  to set `self._has_compatible_ruleset`. It initially looked like it might be
  dead/renamed-and-abandoned scaffolding; it is not.
- **`EngineRunner` (`app/services/engine.py`) is genuinely load-bearing**,
  exercised by `engine/tests/test_designer_third_entrant_command.py` and
  `engine/tests/test_pmars.py`. It is not obsolete.
- **`work/` (repo root) is not part of the Git-tracked repository at all** —
  it is listed in `.gitignore:41` (`/work/`) and contains historical local
  qualification-run scratch data (e.g. `Beta3 Installer Data`,
  `alpha3-release-verify`, `beta3-final-wheel-venv`, stray `.log`/`.xml`
  artifacts). `git status --ignored` confirms it as `!!` (ignored), which is
  why the otherwise-clean `git status` at the top of this report does not
  mention it. This directory is out of scope for any tracked-repository
  cleanup phase; it is mentioned only so a future phase does not mistake it
  for an untracked-but-relevant discovery. No action recommended.
- **Repo-root `agents/`'s extra (non-starter) entries have not yet been
  checked for indirect references** (docs, fixtures, or research reports
  that might name them) — this is explicitly left as unresolved
  (Category B, "must have evidence that they are truly unused") rather than
  assumed dead. Flagged for Phase 1's reference-check pass, not Phase 1's
  deletion pass.
- **No other initially-plausible "looks dead" candidate was found to have
  hidden live references** in this pass. In particular, `sync_ruleset_choices`
  (the *old* name) and `release_notes.txt` were checked and found to not
  exist at all, rather than existing-but-unreferenced.

---

## G. Maintenance invariants

The twelve invariants below apply to all Phase 1–3 work. Numbers 1–12 restate
the task brief's own list (verified as correct and necessary against this
repository); 13–15 are repository-specific additions this inspection showed
are needed.

1. Same seed + same agents + same configuration must produce the same match
   result as the current baseline (Section A's HEAD, `198a94e`).
2. No Ruleset semantics may change (`bytefray-rules-1/2/4/4-alpha1/4-alpha2`).
3. No Agent API semantics may change (v1 `MatchContext`, v2 `MatchContextV2`/
   `ActionKindV2`/`declare_processes()`).
4. No scoring, termination, scheduler, deployment, observation, territory, or
   process behavior may change.
5. Existing Alpha 1 replay files must remain readable unless separately
   approved.
6. Replay interpretation must not silently change.
7. Existing Designer/CLI Alpha 1 workflows and defaults must not change as an
   incidental cleanup effect.
8. Parameter and preset semantics must remain unchanged (including the
   now-corrected cross-frontend consistency `e67787e` established — a future
   cleanup must not regress tournament/`agents test`/`agents evaluate` back
   to resolving `{}`).
9. Cleanup must not remove compatibility behavior merely because it appears
   old without proving its current support status (e.g. `bytefray-rules-2`'s
   API-v1 default status, or the `--pygame` no-op flag's continued
   acceptance).
10. Historical research evidence should generally be archived/preserved
    rather than destroyed (`docs/archive/`, `_legacy/`).
11. Every executable cleanup change in later phases must have evidence
    demonstrating behavioral neutrality (a passing regression test that
    would fail without the fix reverted, or an equivalent characterization
    run, not merely "the diff looks safe").
12. Gameplay improvements suggested during this work should be recorded for
    later consideration, not implemented (see Section J and the existing
    "Suggested backlog" in `V5_ALPHA1_POST_RELEASE_HARDENING_AUDIT.md`
    Section J, which already serves this purpose and should be the landing
    place for any new ones rather than a duplicate list).
13. **A cleanup phase must not assume current HEAD is the published Alpha 1
    artifact.** Any change reasoning about "what Alpha 1 users experienced"
    must be checked against tag `b5.0.0-alpha1` (`28a10b8`), not just HEAD,
    given the divergence documented in Section A.
14. **Presentation-only Replay Viewer changes (rendering, not
    schema/semantics) are the one category of "Replay" work this repository
    has already shown can proceed without violating the gameplay-neutrality
    invariants** (`0d94d6a` is the precedent) — but each such change still
    needs its own explicit demonstration that no replay content, tick
    advancement, or playback-state value changed, not merely that it "looks
    like rendering."
15. **A cleanup phase must re-verify a prior audit's findings against
    current source before acting on them**, per the standing discipline
    `V5_POST_RELEASE_H1_PARAMETER_CONSISTENCY.md` itself established and
    applied to its own predecessor audit. This report already applied that
    discipline to FIND-03 through FIND-07 (Section E) rather than trusting
    the prior audit's text unchecked.

---

## H. Replay History boundary

**Permitted during the Alpha 1 feedback window (research/design only):**

- Reading and documenting current replay creation paths (`telemetry.py`,
  `match_service.py`'s process-result builder, `_run_python_match_traced`).
- Reading and documenting the current replay schema (schema v4;
  `docs/REPLAY_SCHEMA.md`) and its historical predecessors (v1–v3).
- Reading and documenting replay metadata shape and where replay/result/
  summary files are actually written (`runs/_designer`, `runs/_loose`, and
  arbitrary explicit `--replay`/`--out` paths — see Section E's installer
  finding for the directories that are *not* actually used).
- Reading and documenting the current loading workflow (`ReplaySession`,
  `PlaybackController` in `client/src/battle_client/player.py`).
- Reading and documenting the Replay Viewer's current interfaces
  (`PygameRenderer`, the perspective/spectator presentation layer).
- Producing a design document, data-model sketch, or research report for a
  future Replay History Browser.

**Prohibited during the Alpha 1 feedback window, deferred to a later,
explicit phase:**

- Modifying the replay schema (would require a new schema version per
  `docs/REPLAY_SCHEMA.md`'s own versioning discipline).
- Changing replay generation (`telemetry.py`, `_build_process_result`, or any
  writer).
- Adding persistence (a replay index, database, or catalog file).
- Altering playback semantics (tick advancement, seek/step behavior beyond
  what `0d94d6a` already established as presentation-only bookkeeping).
- Any gameplay change.
- Adding database/index files of any kind.
- Implementing any part of the browser itself (UI, storage, or search).

---

## I. Recommended Phase 1 scope

Documentation/repository cleanup items that can proceed next without
touching any protected behavior surface:

1. Rewrite `SECURITY.md`'s "Supported release line" section to state the
   actual current state: stable line is `4.x` (`4.0.0`), current prerelease
   is `5.0.0a1` (Alpha 1), and reference the current Ruleset set
   (`bytefray-rules-4` permanent, with `-4-alpha1`/`-4-alpha2` still
   explicitly selectable) rather than naming only `4.0.0-rc1`/`-alpha1`.
2. Verify (not yet remove) whether `--pygame`'s help text in
   `engine/src/battle_engine/cli.py:304-308` can be tightened for clarity;
   confirm via a full repo grep that no other file reads the parsed
   `args.pygame` value before touching even the help text, since this
   report's finding here was not exhaustive.
3. Reference-check every non-starter entry under repo-root `agents/`
   (`Nemesis`, `bomber`, `chatgpt_hunter`, `claude_agent`, `hydra`,
   `hydra_alpha2`, `nemesis_alpha2`, `replicator`, `viper`) against docs,
   tests, fixtures, and `research/` reports before proposing any of them for
   B-level removal in a later phase. Produce a per-agent evidence table; do
   not delete anything in Phase 1 itself.
4. Do a full (not grep-sampled) repo-wide search for stale doc cross-links
   now that `ec89438` ("clarify historical documentation boundaries") and
   `75f5a2d` ("clean repository and release surface") have already made two
   passes at this — confirm no further broken references were introduced
   since, using the same zero-broken-references check those commits already
   ran.
5. Verify `EngineRunner` (`app/services/engine.py`) has no internal
   obsolete/superseded code path (this Phase 0 pass confirmed the class
   overall is live but did not do a line-level audit of it).

None of the above touches `engine/src`, `client/src` gameplay code, replay
data, agent behavior, Designer/CLI defaults, or version metadata.

## Recommended Phase 2/3 scope (for later, not this report's action)

- FIND-03/FIND-04 (`starters.py` atomicity and content-filtering) — Phase 2,
  behavior-neutral code cleanup, needs new interruption-simulation and
  case/suffix regression tests before any change.
- FIND-05/FIND-06/FIND-07 (packaging/build-script parity and asset scope) —
  Phase 3, release-surface cleanup, needs a real installer/build re-run as
  evidence, not just unit tests.
- Installer's dead `replays`/`logs` directory creation — Phase 3.

---

## J. Deferred items

Anything that could affect Alpha 1 behavior, or requires a separate
architectural/product decision, and is explicitly **not** for Phase 1–3
cleanup:

- **The `--pygame` CLI flag's removal** (as opposed to a help-text edit) —
  changes CLI argument-acceptance behavior; a product decision about closing
  a compatibility surface, not a cleanup.
- **Whether current HEAD or the published tag `b5.0.0-alpha1` is "the"
  frozen Alpha 1 baseline** going forward (Section A) — a decision only the
  user can make; this report recommends HEAD but does not assume it.
- **All items in `V5_ALPHA1_POST_RELEASE_HARDENING_AUDIT.md` Section J's
  existing "Suggested backlog"** beyond what Section E already re-verified
  as still-open (FIND-03 through FIND-07) — that document remains the
  authoritative backlog; this report does not duplicate or supersede it.
- **Gameplay improvements** — none were discovered as a side effect of this
  investigation; if any surface during Phase 1–3, they belong in the same
  backlog document referenced above, not in a new list, and must not be
  implemented while Alpha 1 feedback is pending.
- **Replay History Browser implementation** — entirely deferred per
  Section H; only research/design may proceed.
- **Repo-root `agents/` extra entries' actual disposition** (keep, archive,
  or remove) — deferred until Phase 1's reference-check (Section I, item 3)
  produces evidence; this report takes no position on any individual agent.
- **The two behavior-affecting post-publication commits (`e67787e`,
  `0d94d6a`)** — already landed, already qualified by their own reports; no
  further action is proposed, but any future work in `starters.py`
  (FIND-03/04) or the parameter-resolution path they touch must treat
  `e67787e`'s corrected behavior as the new invariant (Section G, #8), not
  the pre-fix behavior.

---

## Validation

- No file under `engine/src`, `client/src`, `app/`, `agents/`, or
  `tools/` was modified by this phase. The only file this phase adds is this
  report.
- No replay, result, or agent file was created, modified, or deleted.
- `git diff --check`: run against the working tree before adding this report
  — clean (no output, exit `0`); the only change this phase introduces is a
  new untracked file, which `git diff --check` does not inspect until staged.
- No generated test artifact (`.pytest-cache/`, `.pytest-tmp/`, `build/`,
  `dist/`) was staged; none of the commands in Section C write inside the
  repository's tracked tree.
