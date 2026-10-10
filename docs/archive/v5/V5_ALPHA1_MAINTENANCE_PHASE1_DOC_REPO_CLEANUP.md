# Bytefray V5 Alpha 1 Maintenance — Phase 1: Documentation and Repository Cleanup

**Status:** Complete. Documentation/repository-surface cleanup only. No
gameplay, Ruleset, Agent API, replay, CLI, Designer, or GUI behavior was
changed. No Python/code file was modified. No commit or push was performed.
**Discipline:** Narrow scope per the Phase 1 brief and
`V5_ALPHA1_MAINTENANCE_PHASE0_BASELINE.md`, which this report re-verified
rather than assumed.

---

## A. Starting state

| Item | Value |
|---|---|
| Branch | `v5-research` |
| HEAD SHA (start and end of this phase) | `198a94ed70bc9e1ae8a26a13fe33094377712b63` |
| Upstream/tracking branch | `origin/v5-research` |
| Ahead/behind upstream | `0` / `0` (exactly up to date, both at start and end) |
| Working-tree state at phase start | One untracked file: `docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE0_BASELINE.md` (the Phase 0 report itself, preserved and treated as authoritative input); otherwise clean |
| Product version (`pyproject.toml`) | `5.0.0a1` (unchanged) |

HEAD matched Phase 0's recorded SHA exactly at the start of this phase — no
drift occurred between phases. Phase 0's conclusions were verified against
this same commit, not assumed stale.

---

## B. Baseline relationship

- Published Alpha 1 artifact: tag `b5.0.0-alpha1` → commit
  `28a10b8f8fd47bf32ec9281dcc21b0645276962c`, published as a GitHub
  prerelease on 2026-09-10 (per Phase 0, Section A).
- Current maintenance baseline: `v5-research` @ `198a94e` (this phase's
  start and end state), 10 commits ahead of the published tag, per Phase 0's
  already-recorded and still-accurate divergence table (two of those ten
  commits are behavior-affecting: `e67787e` parameter-consistency fix and
  `0d94d6a` presentation-only Replay Viewer capture-callout change — both
  pre-date this phase and were not touched, reverted, or built upon).
- Gameplay/Ruleset semantics are confirmed unchanged by this phase: no file
  under `engine/src`, `client/src` (gameplay/replay-semantic paths),
  `app/` (excluding the read-only inspection recorded in Section G below),
  or `agents/` (tracked fixtures) was modified. The only tracked-content
  changes this phase makes are prose in `SECURITY.md` and the removal of
  two orphaned, unreferenced documentation screenshots (Section I).
- No post-Alpha-0 maintenance commits landed between Phase 0 and Phase 1 —
  HEAD did not move, so there is nothing new to reconcile beyond what
  Phase 0 already recorded.

---

## C. `SECURITY.md`

**Stale issues found** (confirmed against `CHANGELOG.md` and `pyproject.toml`,
not assumed from Phase 0's text alone):

- "Supported release line" claimed the active line was "the `4.x`
  prerelease series, currently `4.0.0-rc1`" and that "the most recent
  stable release remains `3.0.0`." Both false: `CHANGELOG.md` shows
  `[4.0.0] - 2026-09-08` shipped stable, and the current prerelease is
  `5.0.0a1` (`pyproject.toml`, README.md's "Development Line" note),
  published as the Alpha 1 GitHub prerelease.
- The Agent API v2 description named only `bytefray-rules-4-alpha1` as
  "the" v2 Ruleset, omitting the now-also-live `bytefray-rules-4-alpha2`
  and the permanent `bytefray-rules-4` (confirmed via each CLI parser's
  `choices=[...]`, matching Phase 0 Section A).

**Changes made:**

- Rewrote the "Supported release line" paragraph to state the actual
  current state (stable `4.0.0`, prerelease `5.0.0a1`/"Bytefray V5 Alpha
  1"), note that V5 builds on unchanged, stable `bytefray-rules-4` gameplay
  rather than a new Ruleset, and point to `docs/COMPATIBILITY.md` and
  `docs/ROADMAP.md` instead of naming a single stale RC identity.
  See [SECURITY.md](../../../SECURITY.md).
- Updated the Agent API v2 bullet in "Security-sensitive areas" to name all
  three Agent-API-v2 Ruleset identities (`bytefray-rules-4-alpha1`,
  `bytefray-rules-4-alpha2`, `bytefray-rules-4`) instead of only the first.

**Current agent trust/security model** (verified against source, not just
restated from the prior text): Bytefray does **not** sandbox agents. Both
supported agent formats run as trusted local code:

- Python agents (Agent API v1 and v2) run in-process or in a worker
  subprocess with the same OS-level privileges and filesystem/network
  access as the host process. Verified directly in source: `agent_worker.py`,
  `supervised_runtime.py`, `agent_validation.py`, and `agent_test.py` each
  independently self-document their optional execution timeout as
  "development-time hang containment, not a security sandbox" — no
  `seccomp`/`chroot`/`setrlimit`/cgroup/container isolation exists anywhere
  under `engine/src`. This is not used on every execution path (`bytefray
  run` and headless tournaments do not run through the worker timeout).
- Redcode (`.red`/`.asm`) agents run via an external pMARS subprocess,
  invoked with an explicit path and argument list, never through a shell.

This matches the pre-existing "trusted local code, not sandboxed" wording
already in the file's "Security-sensitive areas" section — that section was
already accurate and did not require a trust-model rewrite, only the
release-line correction above and the three-Ruleset naming fix.

**Deferred security concerns:** none newly identified. No sandboxing or
security-architecture change was made or proposed, per the Phase 1
constraint against implementing security architecture changes in this
phase.

---

## D. Documentation/reference audit

**Scope:** every tracked Markdown file's links, image references, and
relative file references; a targeted grep sweep of current-product docs
(`README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `INSTALL.md`,
`CONTRIBUTING.md`, `CHANGELOG.md`, `docs/COMPATIBILITY.md`,
`docs/ROADMAP.md`, `SECURITY.md`) for stale version/release wording;
tracked screenshot assets for orphaned (unreferenced) files.

**Tools/commands used:** no dedicated link-checker exists in this
repository (checked `tools/` and `*test*.py` for one; none found). A
purpose-built read-only Python script
(`check_md_links.py`, run from a scratch directory outside the repository,
not committed) was used to extract every `[text](target)` and `![alt](src)`
reference from all 176 git-tracked `*.md` files and resolve each
non-URL/non-anchor target against the source file's directory, then the
repo root, matching how GitHub and most Markdown renderers resolve relative
links. `git grep` was used to reverse-check whether each tracked screenshot
under `docs/screenshots/` is referenced by any tracked file of any type.

**Defects found:**

- **Zero broken relative Markdown links or image references.** 514
  relative/local link targets across 176 tracked Markdown files all
  resolved. This confirms the two prior cleanup passes (`ec89438`
  "clarify historical documentation boundaries", `75f5a2d` "clean
  repository and release surface") left no regressions, and none have been
  introduced since.
- **Two orphaned, superseded screenshot files**:
  `docs/screenshots/v4-agent-designer.png` and
  `docs/screenshots/v4-replay-perspective.png`. See Section I for the full
  evidence trail and disposition (removed).
- `SECURITY.md`'s stale release-line prose (Section C above) — the only
  substantive prose defect found outside the screenshot orphans.

**Fixes made:** `SECURITY.md` prose (Section C); removal of the two
orphaned screenshots (Section I). No other current-product documentation
file required a correction — the repo-wide link sweep found no additional
broken cross-references, stale CLI examples, or stale ruleset naming in
current product/developer docs.

**Historical files intentionally left unchanged:** every file under
`docs/archive/` and `docs/research/` (including the v3-alpha2 screenshot
set discussed in Section I, and all "as of `v4.0.0-rc1`"-style historical
markers in `AGENTS.md`, `docs/COMPATIBILITY.md`, and `docs/ROADMAP.md` that
correctly narrate *when* something changed rather than asserting it as the
current state). These were read and considered, not skipped by pattern
alone — each "vN.N.N-rcN"-style hit outside `SECURITY.md` was individually
checked and found to be accurate historical narration, not a stale claim
about current state, and was left untouched per the instruction not to
"modernize" historical evidence.

**Note, not acted on:** `CHANGELOG.md` has no `[5.0.0a1]` entry — the file
currently ends its "current" section at `[4.0.0] - 2026-09-08`, with Alpha
1's release notes living only in the GitHub prerelease body (per Phase 0,
Section A). This is a content gap, not a broken reference, and drafting
retroactive release-note prose is a product-content decision outside this
phase's "correct stale documentation" mandate — recorded here for
visibility, not fixed.

---

## E. `--pygame`

**Declaration:** `engine/src/battle_engine/cli.py:304-308` (current `bytefray
run` CLI), `action="store_true"`, `help="(deprecated/no-op) rendering moved
to \`bytefray replay\`"`.

**Call path:** A full-repository grep for `args.pygame`/`.pygame` usage
found exactly one place in the entire tracked tree that reads a parsed
`args.pygame` value: `_legacy/main.py:117`
(`renderer = PygameRenderer() if args.pygame else None`). That is a
**different, frozen legacy dispatcher** (`_legacy/` — frozen historical
code per `AGENTS.md`), not the current product's `engine/src/battle_engine/cli.py`.
The current product's `--pygame` flag is parsed into `args.pygame` and then
never read anywhere else in `cli.py` or the rest of `battle_engine` —
confirmed by grepping the whole tree, not sampling.

**Live/no-op determination:**
- In the **current product CLI** (`bytefray run`), `--pygame` is a
  confirmed, total no-op: accepted, parsed, and discarded.
- The identically-named `--pygame` flag in `_legacy/main.py` (a separate
  argparse declaration, `_legacy/main.py:13`) **is live** — it actually
  constructs a `PygameRenderer`. `tournament/scripts/round_robin.sh`,
  `test_hunter.sh`, and `cla-vs-cgpt.sh` still invoke `_legacy/main.py`
  directly and pass `--pygame` to it (`PYGAME_FLAG="${PYGAME_FLAG:---pygame}"`).
  This is expected: those scripts predate the current CLI and are frozen
  historical/legacy tooling, not confused with the current-product flag.

**Tests:** no test in `engine/tests` or elsewhere exercises the current
product's `bytefray run --pygame` flag specifically (grepped `*cli*` test
files for "pygame": no matches). No test depends on its no-op behavior.

**Documentation:** no current-product documentation (README, AGENT_AUTHORING,
MANUAL_SMOKE_TESTS, etc.) shows `--pygame` as a usage example for `bytefray
run`. The only non-legacy, non-archival mentions are Phase 0's own report
and this report.

**Scripts/packaging:** `tournament/scripts/*.sh` invoke it against the
*legacy* dispatcher (live there, as above), not the current CLI. No build
or packaging script references the current CLI's `--pygame`.

**Compatibility considerations:** removing the argument from
`engine/src/battle_engine/cli.py` would turn `bytefray run --pygame ...`
from "silently accepted no-op" into a hard argparse error for anyone who
still has it in a saved command line, a shell alias, or copied from an old
tutorial — a real (if narrow) compatibility break for zero behavioral gain,
since the flag already does nothing today.

**Recommendation:** **KEEP**, unchanged, exactly as Phase 0 recommended.
The current help text — `"(deprecated/no-op) rendering moved to \`bytefray
replay\`"` — already accurately states both its no-op status and the
correct current replacement command; no help-text wording change was
needed or made. This is confirmed-intentional compatibility surface (a
soft off-ramp for old invocations), not stale interface residue. No
behavioral or textual change was made to the flag in this phase, per the
explicit prohibition on removing or changing it.

---

## F. Repo-root `agents/` audit

**Structural finding, established before the per-entry audit:** repo-root
`agents/` is wholesale git-ignored (`.gitignore:32`, `/agents/`, with the
comment "Source checkouts use root agents/ as the writable runtime
catalogue... Existing tracked historical/reproducibility fixtures remain
tracked"). Of the 29 directories present in the local working tree, **only
5 are actually tracked in Git**: `Nemesis`, `hydra`, `hydra_alpha2`,
`nemesis_alpha2`, `viper` (`git ls-files agents/` confirms exactly these
10 files: one `agent.py` + one `agent.yaml` per directory). The remaining
24 are untracked/ignored local working-tree content — not part of the
repository Git tracks, regardless of what is physically present in this
checkout.

| Path | Tracked? | Purpose | Live references | Packaged? | Classification | Recommendation |
|---|---|---|---|---|---|---|
| `agents/Nemesis`, `agents/hydra`, `agents/viper` | Yes | Historical (pre-alpha2) reference agents authored for Ruleset `bytefray-rules-4-alpha1`'s fixed opposite-core placement assumption | **Live.** Directly loaded by `engine/tests/test_v4_stable_ruleset_equivalence.py` (`REPO_ROOT / "agents"` is one of its two agent-source roots, line 58-61) and named in `tools/v4_alpha2_ecology_study.py`'s `HISTORICAL_ROSTER`; documented by name in `docs/V4_ALPHA2_DESIGN.md`/`docs/COMPATIBILITY.md` as the frozen pre-adaptation baseline | No (repo-root `agents/` is explicitly runtime/user data per `AGENTS.md`, never packaged) | **TEST/QUALIFICATION ASSET** (also historical/research) | **RETAIN — no action.** Load-bearing regression-test fixture; deleting it would fail `test_equivalence_for_hydra_vs_nemesis` and related parametrized tests immediately |
| `agents/hydra_alpha2`, `agents/nemesis_alpha2` | Yes | Alpha2-adapted derivatives of the above, using API v2 visibility/READ-probe target acquisition instead of the opposite-core assumption | **Live.** Same test (`test_equivalence_for_hydra_vs_nemesis`) and `tools/v4_alpha2_ecology_study.py`'s `ADAPTED_ROSTER`; documented in `docs/V4_ALPHA2_DESIGN.md`/`docs/COMPATIBILITY.md` | No | **TEST/QUALIFICATION ASSET** | **RETAIN — no action.** Same live-test dependency as above |
| `agents/bomber`, `agents/chatgpt_hunter`, `agents/claude_agent`, `agents/replicator` | **No** (untracked, git-ignored) | Unknown/orphaned — each contains only opaque `model.blob`/`<name>.blob` files (21-446 bytes), **not** the `agent.py`/`agent.yaml` format every current agent (starter or fixture) uses | **None found.** A repo-wide `git grep` for each name found only unrelated same-named things: `bomber`/`chatgpt_hunter`/`claude_agent` in `tournament/roster.json`/`derived.csv`/scripts refer to a VM **builtin** (`bomber`) or to `_legacy/agents_tooling/*.asm` Redcode files — structurally unrelated to these blob-only directories, which nothing loads by path | No (not tracked at all) | **UNKNOWN / NEEDS LATER REVIEW** — not repository content | **Not part of the tracked repository — no repository-cleanup action applies.** These are local, git-ignored working-tree files, not part of what Phase 1 governs. Per the phase brief's instruction to preserve pre-existing user work and not discard untracked local files without clear authorization, **left untouched**. Flagged only for the user's own awareness in case they want to clear stale local scratch files manually |
| `agents/adaptive`, `claimer`, `hunter`, `raider`, `runner`, `seeker`, `sentinel`, `spiral`, `strider`, `wanderer`, `writer`, `v4_claimer`, `v4_concentrated_attacker`, `v4_defender_scout`, `v4_local_defender`, `v4_quorum`, `v4_scout`, `v5_core_defender`, `v5_dual_team`, `v5_region_attacker`, `v5_scout_striker` (21 dirs) | **No** (untracked, git-ignored) | Runtime mirror of the packaged starter catalogue | Names match `engine/src/battle_engine/data/starter_agents/` **exactly** (verified by directory listing diff) | N/A — these *are* the packaged starters' runtime copies, mirrored by `starters.py`'s `_mirror_bundled`/`ensure_starter_agents` (Phase 0's FIND-03 subject) | **CURRENT PRODUCT** (runtime-generated copy) | **RETAIN — no action; expected, self-regenerating runtime behavior**, not repository content requiring cleanup |

**Summary:** the two prior "extra entries" candidate categories Phase 0
left unresolved (`Nemesis`/`bomber`/`chatgpt_hunter`/`claude_agent`/
`hydra`/`hydra_alpha2`/`nemesis_alpha2`/`replicator`/`viper`) resolve
cleanly: the 5 that are actually tracked in Git are all confirmed live
qualification fixtures (retain), and the 4 that are not tracked are opaque,
unrelated, untracked local files outside this phase's authority to remove.
Nothing under repo-root `agents/` was deleted, moved, or modified.

---

## G. `EngineRunner`

**Where it is defined:** `app/services/engine.py:20`, a `QObject` subclass
(`Popen`+`threading`-based subprocess runner with `output_line`/`finished`/
`error` Qt signals), 108 lines total.

**Who imports/calls it — corrected from Phase 0:** a full-repository grep
for the literal string `EngineRunner` found exactly three occurrences in
the entire tracked tree: the class definition itself; a docstring in
`engine/tests/test_designer_third_entrant_command.py:17` that **explicitly
states** `build_engine_command`'s "only in-repo caller is
`EngineRunner._build_engine_cmd`, which nothing currently instantiates";
and a code *comment* (not a call) in `engine/tests/test_pmars.py:306`
noting a design parallel. A targeted search for `EngineRunner(` (an actual
instantiation) found **zero matches anywhere** — no GUI view, window, or
test constructs an `EngineRunner`. `git log` shows the file's last
substantive change was `6feb10b` ("fix: wire Agent Params through to
matches; remove sdk/; ruff debt strategy"), well before the v4/v5 work.

This is independently and explicitly confirmed by
`docs/specs/agent_designer_workflow.md` §2.9 and its final backlog section:
*"`app/services/engine.py`'s `EngineRunner` (a `Popen`+`threading`-based
runner)... [is] never instantiated by `AgentDesigner`. The live
match-launch path is entirely the `QProcess` path in
`app/agent_designer.py` itself... `EngineRunner` is dead code kept for
historical reasons"* and later: *"is entirely dead code superseded by the
QProcess path in `app/agent_designer.py`... candidate for removal in an
unrelated cleanup pass."*

**Runtime role, accurately stated:** `EngineRunner` the class is currently
**not exercised by any live code path** in this repository. What *is* live
is two of the three names `app/services/engine.py` imports and
re-exports from `app/services/engine_commands.py` — `RunConfig` (used by
`app/views/advanced.py`, `app/views/simple.py`) and
`open_pygame_client_direct` (used by `app/agent_designer.py`,
`app/views/advanced.py`) — both of which are actually *defined* in
`engine_commands.py`, not `engine.py`. The live Designer/GUI match-launch
path is entirely `app/agent_designer.py`'s own `QProcess`-based
`_start_process`-style methods (`build_designer_match_arguments` +
`QProcess`/`QProcessEnvironment`), which do not go through `EngineRunner`
or `build_engine_command` at all.

**Why Phase 0's "load-bearing" conclusion needs correction:** Phase 0
(Section F) cited `test_designer_third_entrant_command.py` and
`test_pmars.py` as evidence `EngineRunner` is load-bearing. Neither test
actually calls or instantiates `EngineRunner`: the first tests
`build_engine_command` directly (a plain function in `engine_commands.py`)
and its own docstring says nothing instantiates `EngineRunner`; the second
only mentions it in an explanatory comment while testing
`battle_engine.cli` subprocess behavior directly. Phase 0's grep-level pass
conflated "the *module* `app/services/engine.py` has live importers" with
"the `EngineRunner` *class* is called" — the module is live only because
other, unrelated names happen to be re-exported through it.

**Legacy/suspicious portions inside it:** none — the class itself is small,
internally consistent, and not further decomposable into a "live part" and
a "dead part." The entire class is the dead sub-element.

**No changes were made.** Per the explicit Phase 1 prohibition, `EngineRunner`
was not refactored, renamed, moved, reinterfaced, or had any branch
removed — this section is inspection and documentation only.

**Phase 2 candidate:** removing `app/services/engine.py`'s `EngineRunner`
class (and, separately/independently, evaluating whether
`engine_commands.py`'s `build_engine_command` is also removable once its
only caller is gone) is a legitimate, already-specified-elsewhere
(`docs/specs/agent_designer_workflow.md` §28) executable cleanup candidate
for Phase 2 — not attempted here. It would need: confirmation no other
branch/tool re-adds a caller, a regression run of `engine/tests` (which
reference it only in comments/docstrings, so removal is expected to be
safe), and care to keep `RunConfig`/`open_pygame_client_direct`/
`build_engine_command`'s own live callers unaffected (those are not
proposed for removal).

---

## H. `sync_ruleset_choices` / `sync_ruleset_choices_for_metadata`

Re-verified at current HEAD (unchanged from Phase 0): the live function is
`sync_ruleset_choices_for_metadata` (`app/widgets/ruleset_combo.py:44`),
called from `app/views/development.py:795` and
`app/views/evaluation.py:323` to set `self._has_compatible_ruleset`. The
old name `sync_ruleset_choices` does not exist anywhere in the tracked
tree, and the existing regression test
(`tests/test_v5_alpha1_phase_e_designer_ux.py:747-754`) still asserts
`not hasattr(module, "sync_ruleset_choices")` alongside
`hasattr(module, "sync_ruleset_choices_for_metadata")`.

**NO ACTION — LIVE.** No refactor was performed, per the explicit Phase 1
prohibition.

---

## I. Repository-artifact cleanup

**Items removed:**

| File | Size | Proof of non-use |
|---|---|---|
| `docs/screenshots/v4-agent-designer.png` | 33,431 bytes | `git grep -in "v4-agent-designer"` (whole tracked tree, case-insensitive, no file-type restriction): zero hits. Added by `a0a14b8` ("docs(rc2): refresh README visuals...") as README's `## Agent Designer` section image; that section and its image reference were removed/replaced by the later v5 README rewrite (`11d2be0`/`0b414a2`, which introduced `docs/screenshots/v5-agent-designer.png` instead under `## Build agents your way`), leaving this file orphaned in the tree with no remaining reference of any kind |
| `docs/screenshots/v4-replay-perspective.png` | 110,422 bytes | Same check, zero hits. Added by the same commit as one half of a Broadcast/Perspective screenshot pair under README's old `## Replay Viewer` section; its sibling `docs/screenshots/v4-replay-broadcast.png` survived by being reused under the current `## Replays and Tooling` section, but this file's reference was dropped during the restructure and never replaced |

Both were current-product (not historical/archival) README illustration
images, confirmed superseded by their v5 replacements via `git log`, and
carried no test, research, release-evidence, compatibility, packaging, or
user-workflow value (`MANIFEST.in`, `pyproject.toml`, and every `tools/*.spec`
were also checked and reference neither file).

**Items explicitly retained and why:**

- `docs/screenshots/v3-alpha2/01-simple-raider-vs-sentinel.png`,
  `03-agent-development-ruleset-v2-default.png`, and
  `04-pairwise-evaluate-ruleset-v2-default.png` are also currently
  unreferenced by any tracked file (their siblings `02-...png` and
  `05-...png` *are* cited by
  `docs/archive/v3/V3_ALPHA2_STRATEGY_EXAMPLES_RULESET_CLARITY.md`).
  **Retained, not removed** — these are part of a historical/archived
  qualification screenshot set (added in `477be68`, a v3-era feature
  commit), and per the Phase 1 instruction to treat historical
  research/qualification evidence conservatively rather than delete
  merely-uncited members of an otherwise-cited evidence set, this is
  recorded as a documented-but-unresolved item rather than acted on.
- All local, git-ignored working-tree content (`work/`, stale
  `rc2-final-win-*.log`/`*.xml` qualification scratch files, `runs/`,
  `agent_revisions/`, `build/`, `__pycache__/` trees, loose
  `replay.jsonl`/`summary.json`/`combat_replay.jsonl` files at the repo
  root, the 4 orphaned blob-only `agents/` directories from Section F) —
  none of this is tracked repository content; per the phase brief's
  instruction not to confuse untracked local artifacts with repository
  content, and to preserve pre-existing user work, **none of it was
  touched**.
- `assets/branding/bytefray-brand-sheet.png` (the 1.16MB file FIND-06
  already flags as over-bundled by two PyInstaller specs) — retained
  as-is; its packaging-scope issue is FIND-06, explicitly a Phase 3 item,
  not a repository-content problem to fix here.

---

## J. Phase 2 candidate list

| Candidate | Source | Risk | Tests likely required |
|---|---|---|---|
| FIND-03 — non-atomic `_mirror_bundled` starter refresh (`engine/src/battle_engine/starters.py:390-414`) | `V5_ALPHA1_POST_RELEASE_HARDENING_AUDIT.md`; re-verified present at current HEAD in this phase | Moderate — touches the starter-refresh path exercised on every product launch | New interruption-simulation regression coverage before any fix, per the audit's own recommendation |
| FIND-04 — `starter_content_files` filters `__pycache__` by exact-case name only, not loose `.pyc`/`.pyo`/case variants (`starters.py:153-164`) | Same audit; re-verified present | Low | Case/suffix regression tests |
| FIND-05 — `tools/build_linux.sh` has no post-build bytecode/debris guard, unlike `tools/build_win.ps1` | Same audit; re-verified present (no `.pyc`/`__pycache__` check in the script) | Low — Linux PyInstaller binaries are not currently CI-gated or released | A real Linux build re-run as evidence |
| FIND-06 — `agent_designer.spec`/`replay_viewer.spec` bundle all of repo-root `assets/` instead of just `app/assets/branding` like `bytefray.spec` | Same audit; re-verified present at current HEAD | Low — binary bloat only | Build size comparison before/after |
| FIND-07 — `packaging_data.py`'s cache-directory check is case-sensitive | Same audit; re-verified present | Very low | Case-variant unit test |
| Installer creates unused `replays`/`logs` data-root subdirectories (`tools/installer.iss:52,54`) | Phase 0, Section E; re-verified present | Low-moderate — release/installer tooling | Installer-lifecycle smoke re-run |
| **`EngineRunner` (`app/services/engine.py`) removal** | This phase, Section G — corrects Phase 0's characterization; independently already recommended by `docs/specs/agent_designer_workflow.md` §28 | Low — confirmed zero live callers via two independent full-repo searches plus an existing spec's own dead-code finding | Full `engine/tests`/`app`-adjacent test run after removal to confirm no hidden caller; no new test should be *needed* since nothing currently depends on it |
| v3-alpha2 uncited screenshot trio disposition (Section I) | This phase | Very low — pure asset question, no code | None; a documentation/product decision about whether to retire, keep, or cite them |
| `CHANGELOG.md` missing a `[5.0.0a1]` entry (Section D) | This phase | None (content gap, not a defect) | None; a product-content decision |

FIND-03 through FIND-07 remain **not implemented**, exactly as instructed.

---

## K. Deferred/high-risk items

- **`--pygame` flag removal** (as opposed to the no-op status this phase
  merely documented) — a product decision about closing a CLI
  compatibility surface, not a cleanup; explicitly out of scope here and
  not touched.
- **Whether current HEAD or the published tag `b5.0.0-alpha1` is "the"
  frozen Alpha 1 baseline going forward** — unchanged from Phase 0; still
  a decision only the user can make, not re-litigated by this phase.
- **All items in `V5_ALPHA1_POST_RELEASE_HARDENING_AUDIT.md`'s Section J
  "Suggested backlog"** beyond FIND-03–07 already re-verified — untouched.
- **Replay History Browser** — no design, storage, schema, or UI work was
  performed; only the pre-existing Phase 0 research-permission boundary
  applies, and this phase did not exercise even that (no replay-path
  research was newly conducted).
- **`EngineRunner` removal itself** — documented as a strong Phase 2
  candidate (Section G/J) but explicitly **not implemented** in this
  phase, per the prohibition on refactoring it here.
- Any GUI/Designer/CLI wording, default, or workflow change — none was
  proposed or made; every change in this phase is confined to
  `SECURITY.md` prose and two orphaned screenshot files.

---

## L. Files changed

| File | Change | Why |
|---|---|---|
| `SECURITY.md` | Modified | Corrected stale "Supported release line" section (false `4.0.0-rc1`/`3.0.0` claims → accurate `4.0.0` stable / `5.0.0a1` prerelease) and updated the Agent API v2 Ruleset naming to list all three current v2 Rulesets instead of only `bytefray-rules-4-alpha1`. See Section C. |
| `docs/screenshots/v4-agent-designer.png` | Deleted | Orphaned, unreferenced, superseded by `v5-agent-designer.png` in the current README. See Section I. |
| `docs/screenshots/v4-replay-perspective.png` | Deleted | Orphaned, unreferenced; its sibling image survived the v5 README restructure but this one's reference was dropped and never replaced. See Section I. |
| `docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE1_DOC_REPO_CLEANUP.md` | Added | This report. |

`docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE0_BASELINE.md` (untracked at
phase start) was left exactly as found — not modified, not staged, not
committed by this phase; it remains the user's to add/commit as they
choose.

No file under `engine/src`, `client/src`, `app/` (beyond read-only
inspection), `agents/` (tracked fixtures), `tools/`, or any test directory
was modified.

---

## Validation

- `git diff --check`: clean, no output, exit `0`.
- Documentation/reference check: custom repo-wide Markdown link sweep (176
  tracked `.md` files, 514 relative/local link targets) — zero broken
  references, before and after this phase's changes (the two files removed
  in Section I had zero references to begin with, so their removal cannot
  have broken a link).
- `ruff check .`: `All checks passed!` — run as a cheap sanity check even
  though no Python file was intentionally changed in this phase.
- No `mypy` invocation or `pytest` run was required or performed: no
  runtime Python/code file was changed, no packaged repository artifact
  (only two unreferenced documentation screenshots) was removed, no agent
  file changed, and no build/install configuration changed. Per the Phase 1
  validation instructions, a full test suite is not automatically required
  solely for prose/asset edits of this kind.

Final state:

```
$ git diff --stat HEAD
 SECURITY.md                                |  27 ++++++++++++++++-----------
 docs/screenshots/v4-agent-designer.png     | Bin 33431 -> 0 bytes
 docs/screenshots/v4-replay-perspective.png | Bin 110422 -> 0 bytes
 3 files changed, 16 insertions(+), 11 deletions(-)

$ git diff --check
(clean, exit 0)

$ git status --short
 M SECURITY.md
D  docs/screenshots/v4-agent-designer.png
D  docs/screenshots/v4-replay-perspective.png
?? docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE0_BASELINE.md
?? docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE1_DOC_REPO_CLEANUP.md
```

No whitespace-only or unrelated formatting churn was introduced — both
diffs were reviewed by hand (Section C's `SECURITY.md` edit, and the two
binary deletions in Section I).
