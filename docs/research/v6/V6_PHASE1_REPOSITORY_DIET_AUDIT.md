# Bytefray V6 Research — Phase 1: Repository Diet Audit

**Status:** Phase 1 — evidence-gathering only. No production source, test, documentation,
asset, configuration, example, ruleset, or generated/runtime material was deleted, moved,
renamed, consolidated, refactored, rewritten, or otherwise modified in this phase. The only
repository change introduced by this phase is this report.

**Branch:** `v6-research`. **HEAD at time of audit:** `ffcbe9f345f5c4e03d6340d9a8d528c381984f34`
(the Phase 0 baseline commit itself — no commits were added between Phase 0 and the start of
Phase 1). **Phase 0 baseline report:** `docs/research/v6/V6_PHASE0_BASELINE.md`.

---

## 1. Executive summary

Phase 1 ran a source-grounded, evidence-first audit across all thirteen areas the Phase 1
charter specified: ruleset identities, documentation, dead code, tests, examples/runtime
state, assets, and packaging/config hygiene. Six independent research passes were run in
parallel, each required to cite `file:line` evidence rather than filename or age-based
guesses; their claims were then cross-checked against each other and, for the highest-impact
items, verified directly against the repository a second time before being written into this
report. That second pass caught and corrected two errors that would otherwise have propagated:
one sub-audit's claim about tracked `.pyc` files was independently falsified (no `.pyc` file is
tracked anywhere in this repository), and Phase 0's own per-directory test-file/LOC breakdown
was found to be internally inconsistent (corrected in §7).

**The headline finding is not about the repository's weight — it's about the reliability of
claims made about it.** Three independent sub-audits, and this report's own direct
verification, converge on the same fact: `client/src/battle_client/renderers/pygame_canvas.py`
— which `ARCHITECTURE.md`, `docs/MANUAL_SMOKE_TESTS.md`, `docs/specs/agent_designer_workflow.md`,
`docs/specs/agent_lab.md`, and **Phase 0's own baseline report** (committed the same day as this
audit began) all describe in the present tense as existing, unremoved dead code — was actually
deleted in commit `468028c` ("Retire obsolete BATTLE2 runtime surfaces"), before `v1.4.0`, well
over a year and four major versions ago. There is nothing to delete. The actionable finding is a
documentation-hygiene one: five live documents assert a false fact about the current tree, and
that false fact was carried forward into this V6 program's own Phase 0 charter without
verification. This is recorded here as the primary case study for why Phase 2 must re-verify
every inherited claim against source, not just this audit's own.

Beyond that, the substantive findings are:

- **All 8 registered Ruleset identities should be KEPT in Phase 2**, with one exception
  (`bytefray-rules-3-alpha1`) marked **INVESTIGATE, leaning EXTRACT-ARCHIVE**. Seven of the
  eight historical/alpha identities share their execution code with a still-supported Ruleset
  (v1, v2, or v4) — there is no separable "old engine" to delete without duplicating code the
  product still needs. Only `bytefray-rules-3-alpha1`'s locality mechanic is genuinely
  self-contained and unused by any live Ruleset, making it the sole realistic extraction
  candidate, but the coupling boundary needs further scoping before Phase 2 can safely act.
- **Two closed research programs (`docs/research/v4/`, 31 files; `docs/research/v5/`, 48
  files — 79 files, ~2.35 MB) were never archived**, breaking a pattern this repository already
  established and successfully executed for v1/v2/v3 (`docs/archive/v4/DOCUMENTATION_INVENTORY.md`
  is the record of that prior, successful pass). This is the single largest, lowest-risk,
  highest-confidence cleanup opportunity found in this audit — it is a relocation, not a
  deletion, and it directly follows a precedent this repository has already validated.
- **`ARCHITECTURE.md` needs a real correction pass, not a header edit.** Beyond the
  already-known stale header (frozen at "through v4.0.0-alpha1"), the document's body is silent
  on ~12,200 lines of shipped code across six subsystems (Spectator/Fight Night, Agent
  Packaging, Agent Parameters, Extended Evaluation Analysis, Replay Integrity, and the
  Placement/Scheduler/Ruleset-Policy modules that `docs/RULES_V4.md` names directly), and it
  contains one outright false claim: it describes the Evaluation History UI as "deferred" when
  it has been shipped and wired into the Designer since the V5 era.
- **A concrete, previously-undiscovered mechanism for Phase 0's own "56 test failures" finding
  was located**: `engine/tests/test_v4_stable_ruleset_equivalence.py`'s starter-agent bootstrap
  helper falls back to the real repo-root `agents/` catalog and checks only `Path.is_dir()`,
  never verifying the directory actually contains `agent.py`/`agent.yaml` — exactly the failure
  mode a stale, emptied local `agents/v4_*` directory would trigger.
- A small number of genuinely orphaned, low-risk items were found with no packaging or test
  dependency: `pmars/windows/pmars-server.exe` plus its unbundled sibling docs (`AUTHORS`,
  `ChangeLog`, `CONTRIB`, `README` — only `pmars.exe`+`COPYING` are actually bundled into the
  Windows installer), the top-level `warriors/*.red` corpus (unreferenced by any test, CI job,
  or doc), one CI workflow (`linux-package.yml`) still push-triggered on a long-abandoned branch
  name, one dead exploratory test file with zero real assertions
  (`test_v4_stage6_observation.py`), and one large (1.17 MB) unreferenced brand asset.
- **Closed-out research tooling** (`tools/v3_closeout_*.py`, `tools/v3_phase3_rescore.py`,
  `tools/v3_phase6_defense_episode.py`, `tools/v3_phase7_confound_isolation.py`,
  `tools/research/v5/*`) has zero callers from any product/CLI/app path, but each still has a
  dedicated, currently-passing test file exercising it directly — a self-contained
  research-script-plus-its-own-test cluster that can be retired together without touching
  `battle_engine`.
- **The `tournament/` directory (root-level, distinct from the live `bytefray tournament` CLI
  feature) is legacy tooling whose build pipeline has quietly bit-rotted** since a prior `sdk/`
  removal deleted its only `build.sh` dependency — but it is still directly unit-tested
  (`engine/tests/test_tournament_btctl.py`), and `docs/TOURNAMENTS.md` already documents it as
  "not the supported execution path." This is a human policy call (retire it, or restore it),
  not a technical one.
- **No dead GUI paths, no stale feature flags, no unremediated duplicated implementations, and
  no closed-window migration code** were found anywhere in `engine/`, `client/`, or `app/`. This
  is a genuinely clean result, not an oversight — see §6 for the negative evidence.

No ruleset, source file, test, or documentation file was removed, and none should be until
Phase 2 makes the removal decisions this report sets up. Several of this report's strongest
findings are, appropriately, judgment calls for a human to make (§13), not conclusions this
audit reaches on its own.

---

## 2. Baseline confirmation

| Check | Result |
|---|---|
| Current branch | `v6-research` |
| Phase 0 commit present | `ffcbe9f345f5c4e03d6340d9a8d528c381984f34` — this **is** current HEAD; no commits were added between Phase 0's close and Phase 1's start |
| Working tree | Clean (`git status --porcelain` empty) at Phase 1 start and confirmed again at Phase 1 close (§14) |
| `origin/v6-research` | **Does not exist.** `git branch -r` lists no `origin/v6-research`; only `origin/main` and other historical branches are present on the remote. Ahead/behind comparison against a remote `v6-research` is therefore not applicable — this branch has not yet been pushed. |
| `main` | Not touched. No checkout, merge, or write operation targeted `main` during this phase. |
| Unrelated local file repair | None performed. The local gitignored `agents/` runtime-catalog gap Phase 0 found and repaired is a separate, prior, already-resolved local-environment condition; Phase 1 did not need to touch it (no test suite execution was required for this static audit — see §14). |

One correction to Phase 0's own baseline surfaced during this phase (§7.1): Phase 0's
per-directory test file/LOC breakdown (`engine/tests`: 159 files/63,467 LOC; `client/tests`: 17
files/9,116 LOC) does not reconcile with its own stated 160-file, 3,709-test total. Direct
recount from `git ls-files` at this same commit gives `engine/tests/`: 143 `test_*.py` files
(62,656 LOC), `client/tests/`: 16 files (9,109 LOC), `_legacy/tests/`: 1 file (17 LOC) — 160
files total, matching the headline count exactly. This is arithmetic drift in Phase 0's report,
not evidence of any file having been added or removed since (`git diff --stat` between Phase
0's starting SHA and this audit's baseline, filtered to test paths, is empty). Phase 2 should
use the corrected 143/16/1 breakdown, not Phase 0 §7's table.

A second Phase 0 discrepancy: Phase 0 §7 reports "18 starter" agent directories; direct
enumeration of `engine/src/battle_engine/data/starter_agents/` finds **21** directories. The
gap is plausibly `v4_quorum` (its own bundled `README.md` calls it "an advanced example rather
than a starter") and `raider`/`sentinel` (documented as intentionally excluded from the frozen
benchmark-identity set) — see §8. This is a definitional inconsistency ("what counts as a
starter"), not a missing/extra file; Phase 2/3 should pick one definition and use it
consistently.

---

## 3. Repository disposition methodology

Six parallel, read-only research passes were run, each scoped to one audit area from the
charter (ruleset identities; documentation; source/dead-code; tests; assets/examples/runtime
state; packaging/config). Each was instructed to:

- cite `file:line` evidence for every claim, not filename- or age-based inference;
- check for dynamic registration, imports, plugin-style dispatch, CLI argument tables, test
  references, and packaging manifests before declaring anything unused — a text-search miss is
  not proof of non-use;
- explicitly mark items **INVESTIGATE** rather than guessing when evidence was insufficient;
- treat Phase 0's own claims (and, by extension, any other prior audit's claims cited within
  the repository, such as `docs/research/v5/V5_ALPHA1_MAINTENANCE_PHASE4_RELEASE_SURFACE_AUDIT.md`)
  as claims to re-verify, not as ground truth.

After all six returned, this report's author (a separate synthesis pass, not any one of the six
sub-audits) cross-checked claims against each other for agreement/conflict, and independently
re-verified the highest-impact and most surprising claims a second time directly against the
repository before including them here (§1, §7.4). One claim from the assets/runtime-state
sub-audit — that four `.pyc` files were tracked under `tournament/scripts/__pycache__/` and one
under `engine/src/battle_engine/data/reference_agents/core_defender/__pycache__/` — was checked
this way and found to be **false**: `git ls-files | grep -i pycache` and `git ls-files "*.pyc"`
both return zero results repository-wide. This claim is nullified and does not appear in this
report's findings or cleanup batches. It is recorded here, rather than silently dropped, as
evidence that the cross-check step is doing real work and to model the same discipline for
whoever re-verifies this report in Phase 2.

The five-bucket disposition taxonomy (KEEP / CONSOLIDATE / EXTRACT-ARCHIVE / DELETE /
INVESTIGATE) is applied per-item in each section below, with the evidence and dependency
reasoning inline rather than deferred to a single master table, because the "why" differs
enough by category (a ruleset's disposition hinges on replay-compatibility law; a doc's hinges
on whether git tags already preserve its facts; a test's hinges on whether the behavior it
guards still exists) that one flat table would flatten the reasoning that makes each
recommendation defensible.

---

## 4. Ruleset audit

`engine/src/battle_engine/ruleset_policy.py:487` registers exactly 8 identities in
`_RULESET_POLICIES` (count independently re-verified against source, confirming Phase 0's
count), plus one comparison-only alias (`evaluation-rules-1` → `bytefray-rules-1`,
`rules.py:106-108`).

### 4.1 Summary

| Ruleset ID | Bucket | GUI | CLI | Dedicated tests | Disposition |
|---|---|---|---|---|---|
| `bytefray-rules-1` | Current supported | Yes — sole VM/blob option | Yes, all 4 `--ruleset` surfaces | Extensive | **KEEP** |
| `bytefray-rules-2` | Current supported | Yes — required for Group evaluation | Yes | Extensive | **KEEP** |
| `bytefray-rules-2-alpha1` | Historical, frozen | No | No (excluded from every `--ruleset choices` list) | `test_ruleset_v2_alpha1.py` (19 funcs) + 10 more files | **KEEP** |
| `bytefray-rules-2-alpha11` | Historical, frozen | No | No | `test_ruleset_v2_alpha11.py` (30 funcs) + promotion-equivalence suite | **KEEP** |
| `bytefray-rules-3-alpha1` | Closed research-only | No | No (not even in `agents evaluate`'s argparse) | `test_v3_phase2_locality_*.py` (3 files, 41+ funcs) + 6 more | **INVESTIGATE**, leaning EXTRACT-ARCHIVE |
| `bytefray-rules-4-alpha1` | Historical, frozen | Yes | Yes | Extensive, incl. historical-immutability pin | **KEEP** |
| `bytefray-rules-4-alpha2` | Historical, frozen | Yes | Yes | Extensive, incl. **release-blocking** equivalence gate | **KEEP** |
| `bytefray-rules-4` | Current supported, default | Yes, all surfaces | Yes | Extensive | **KEEP** |
| `evaluation-rules-1` (alias) | Comparison-only, legacy wire value | N/A | N/A | `test_rules.py`, comparison tests | **KEEP** |

### 4.2 The decisive question: does replay compatibility require the full engine?

Item 12 of the charter asked the sharpest version of this question directly: would removing a
ruleset's live execution code break *reading* existing recorded data, or only prevent *creating*
new matches under that identity? The ruleset audit traced this at the source level and found a
clean answer: **replay/result reading never invokes the gameplay engine for any ruleset.**
`ReplaySession`/`ReplayPlayer` (`client/src/battle_client/session.py`, `player.py`) reconstruct
state purely from persisted `MemoryDiff`/tick records and import zero symbols from
`ruleset_policy.py` or any scheduler/execution module. The only engine import on the replay-read
path is a handful of small, side-effect-free helpers (`has_vulnerable_core`,
`has_observable_core`, `core_addresses`, `CORE_SIZE` from `python_runtime.py`) consumed by
`client/src/battle_client/replay_status.py:38`. `docs/COMPATIBILITY.md:28-31` states this
design intent explicitly: "Recorded replay playback reconstructs stored state without
re-executing agents... Keeping an identity readable and preserving its interpretation is
distinct from offering it for new matches."

This means a Phase-2 "extract to archive, keep only a reader" strategy is *structurally
possible* for every one of the 8 identities — but whether it's *worth doing* differs sharply by
identity:

- For `bytefray-rules-2-alpha1`, `-2-alpha11`, `-4-alpha1`, and `-4-alpha2`: the "full engine"
  is not separable from the still-supported `bytefray-rules-2`/`bytefray-rules-4`. Their
  scheduler/placement/core-mechanic dispatch is field- and frozenset-driven, not per-identity
  code (`ruleset_policy.py:9-17`; `python_runtime.py:109-266`'s `VULNERABLE_CORE_RULESET_IDS`/
  `OBSERVABLE_CORE_RULESET_IDS` membership sets). Extracting these would mean **duplicating**
  code the product still runs today, not removing anything. Retaining their registry entries
  costs essentially nothing and, for `-4-alpha2` specifically, is the frozen "before" half of
  `test_v4_stable_ruleset_equivalence.py` — the release-blocking proof that promoting alpha2 to
  permanent `bytefray-rules-4` introduced no gameplay drift. For `-2-alpha11` specifically, the
  same relationship holds via `test_ruleset_v2_promotion_equivalence.py`, which
  `docs/COMPATIBILITY.md:251-257` cites as the evidentiary backbone for permanent v2's contract.
  **These four are zero-cost KEEPs, not merely low-cost ones.**
- For `bytefray-rules-3-alpha1`: this is the one identity in the inventory where the mechanic
  (the locus/reach/`LOCAL_READ`/`LOCAL_WRITE`/`MOVE` block at `python_runtime.py:154-230+`,
  gated by its own `LOCALITY_RULESET_IDS` frozenset) is **not shared with any currently-supported
  ruleset** — it exists solely to run this one closed-research identity. It is never exposed on
  any GUI surface, never in any CLI `--ruleset` choices list (confirmed by grep across every
  argparse `choices=[...]` table in `cli.py`, `tournament_cli.py`, `agent_test.py`, and
  `agent_evaluation.py`'s CLI parser), and its own registration comment
  (`ruleset_policy.py:333-335`) says outright: "closed research-only identity; never exposed on
  any product CLI `--ruleset` choice; no stable Ruleset 3 exists." `docs/archive/v3/
  V3_RESEARCH_CLOSEOUT.md` is the formal closeout record: the research question this identity
  existed to test is closed, and no stable Ruleset 3 followed it.

### 4.3 Disposition and the one open item

Eight of the nine identities (including the alias) are **KEEP** with no further action needed —
either they are the current product default, or their apparent "historical implementation" is
in fact zero marginal engine code riding on a shared, still-supported mechanic.

`bytefray-rules-3-alpha1` is marked **INVESTIGATE, leaning EXTRACT-ARCHIVE** rather than a firm
recommendation, because the ruleset audit did not measure the exact coupling boundary between
the locality mechanic block in `python_runtime.py` and the shared scheduling/core code closely
enough to certify a clean extraction is low-risk. Phase 2 should scope specifically: (a) the
precise line/dependency boundary of the locality mechanic, (b) what the 6 dedicated packaged
agents (`v3_locality_agents/`) and their 3 defining test files would need if relocated to an
archival/research package, and (c) confirmation that a minimal replay-classification shim (the
ID string plus a `LOCALITY_RULESET_IDS`-equivalent membership check, no execution) is sufficient
for `replay_status.py`/`resolve_replay_ruleset` to keep working. Note this is distinct from, and
should not be conflated with, the separately-closed **v3 research tooling** cluster (§6.5, §9) —
the ruleset itself and the standalone research scripts that once studied it are different
things with different removal mechanics.

The `evaluation-rules-1` alias is a one-line dict entry (`rules.py:106-108`) with a narrow but
real cost of removal: it is what lets `evaluations compare` correctly align any pre-v0.10
`bytefray.evaluation` artifact still on a user's disk against a fresh run
(`docs/COMPATIBILITY.md:619-631`). Removing it would not affect any execution path, but would
silently misclassify real historical data as a "changed condition" instead of a match. **KEEP** —
trivial retention cost, real narrow correctness value.

---

## 5. Documentation audit

**207 tracked Markdown files** (`git ls-files -- '*.md'`, independently recounted; Phase 0's
own baseline document counts itself as 206, a 1-file self-reference discrepancy, immaterial),
totaling 5,828,381 bytes / 100,528 lines. **190 of the 207 (94.8% of bytes) live under `docs/`.**
No exact-duplicate file exists anywhere in the tree (verified via `git hash-object` comparison
across all 207 files — zero collisions) and no zero-byte files exist today.

### 5.1 Category breakdown

| Category | Files | Bytes | Notes |
|---|---:|---:|---|
| Top-level product docs (root: AGENTS.md, ARCHITECTURE.md, CHANGELOG.md, etc.) | 8 | 272,288 | All current, actively maintained |
| Current reference/guide docs (`docs/*.md`, direct children) | 22 | 433,282 | |
| Specs (`docs/specs/`) | 16 | 592,367 | Function as permanent design-reference docs for shipped features, not purely forward-looking (see §5.5) |
| Release records (`docs/releases/`) | 2 | 4,704 | |
| Active research (`docs/research/v6/`) | 1 | 28,700 | The only genuinely open research content in the repository |
| **Closed research, not yet archived** (`docs/research/{v4,v5}/`) | **79** | **2,347,799** | **See §5.2 — the single largest finding of this section** |
| Historical archive (`docs/archive/{v1,v2,v3,v4}/`) | 70 | 2,119,765 | See §5.3 |
| Misc supplementary READMEs, prompt/issue templates | 8 | ~32,000 | |
| **Total** | **207** | **5,828,381** | |

### 5.2 The archive gap: `docs/research/v4/` and `docs/research/v5/`

`docs/archive/{v1,v2,v3}/` (16 + 28 + 23 = 67 files, independently recounted and matching Phase
0) are consistently, correctly archived — and this is not an accident: `docs/archive/v4/
DOCUMENTATION_INVENTORY.md` (135 lines) is itself the surviving record of a prior full-repo
documentation classification pass, performed at the v4-alpha era, that produced exactly this
v1/v2/v3 archive structure. Its own recorded counts (`ARCHIVE_V1=15`, `ARCHIVE_V2=28`,
`ARCHIVE_V3=23`) still match what's on disk today (the v1 count differs by one — 16 vs. 15 —
plausibly one file added since; not investigated further as immaterial). **This prior pass is
direct, in-repository precedent that this exact kind of consolidation is low-risk and has
already succeeded once in this codebase.**

That precedent was never extended to v4 or v5. `docs/archive/v4/` holds only 3 files (the old
inventory doc plus 2 cherry-picked qualification reports); the other **31** v4 research files
remain under `docs/research/v4/`. `docs/archive/v5/` **does not exist at all** — all **48** v5
research files remain under `docs/research/v5/`. Both v4.0.0 and v5.0.0 are fully shipped and
tagged (`v4.0.0`, `v5.0.0` among the 39 tags confirmed via `git tag --list`), and both are
superseded by later work; `v6-research` has already begun. This is a structural inconsistency
against the repository's own established pattern, not a judgment call about whether the content
still has value — the fact-preservation check (git tags + `CHANGELOG.md` + the design docs that
absorbed each program's conclusions) is satisfied the same way it was for v1/v2/v3.

Notable clusters within the 79 unarchived files, for Phase 2 batching purposes:

- **v4 process-model foundational research** (7 files) — feeds the still-live `V4_ALPHA1_DESIGN.md`.
- **v4 Spectator/Fight-Night research** (11 files, one of the largest single clusters) — has
  **no closeout/summary document**, unlike v3's `V3_RESEARCH_CLOSEOUT.md`. Flagged INVESTIGATE:
  consider writing a short synthesis before/instead of archiving 11 separate phase files verbatim.
- **v4 RC1/RC2 qualification** (11 files).
- **V5 Alpha 1 maintenance/hygiene program** (18 files — the largest single-program cluster in
  the repository; already has a synthesis document, `V5_ALPHA1_CONSOLIDATION_AND_PLAN.md`,
  though whether that document already supersedes the need for all 18 individual phase reports
  is INVESTIGATE, not confirmed in this pass).
- **V5 Replay History program** (7 files, ~330 KB) — `ARCHITECTURE.md:244` points directly at
  one of these (`V5_REPLAY_HISTORY_PHASE6_ARCHITECTURE.md`) as its design record. **Must be
  relocated, not deleted**, and any archive move must update that live cross-reference.
- **V5 RC1 and Final qualification** (10 files); **V5 gameplay-adjacent research** (4 files).

### 5.3 `ARCHITECTURE.md` — full itemized findings

Read in full (931 lines) by the documentation sub-audit and independently spot-checked against
source by this report (§1, §7.4). Verdict: **more than a header fix, less than a rewrite.**

1. **Stale header (lines 1–24, confirmed verbatim in this report's own re-read):** states the
   document "describes Bytefray's architecture through v4.0.0-alpha1," with a milestone list
   stopping at "v0.7." Current `pyproject.toml` version is `5.0.0`; the branch is `v6-research`.
   Not updated across `v4.0.0-alpha2` through `-alpha4`, `-rc1`, `-rc2`, final `v4.0.0`, or all
   of `v5.0.0`.
2. **Body coverage gap (not just the header):** cross-checked against the live
   `engine/src/battle_engine/` tree, roughly **12,200 lines across 17 modules** are shipped,
   real, cross-referenced-by-other-current-docs code that `ARCHITECTURE.md`'s "Runtime
   Components" section never names:

   | Module(s) | Lines | Feature area | Confirms shipped via |
   |---|---:|---|---|
   | `spectator_aggregation.py` + 5 siblings | 4,459 | Spectator Director / Perspective Cam / Fight Night | `docs/ROADMAP.md:1132-1211`, 14 `CHANGELOG.md` mentions |
   | `agent_package.py` + `agent_package_cli.py` + view | 1,627 | Agent packaging/export | `docs/FUTURE_PLANS.md:60-82` ("shipped v1.2.0"), `docs/specs/agent_package.md` |
   | `agent_parameters.py` | 732 | Parameterization/presets | `README.md` "Parameters and Presets" section |
   | 6 `evaluation_*` extension modules | 3,404 | Analysis/behavior-profiling/presets/parallel worker | `docs/FUTURE_PLANS.md:86-153` |
   | `replay_integrity.py` + view | 207 | Replay/result digest verification | Described in prose elsewhere in `ARCHITECTURE.md` but the module itself never named |
   | `entrant_identity.py`, `placement.py`, `reference_agents.py`, `benchmarks.py`, `scheduler.py`, `ruleset_policy.py`, `rules.py` | 2,136 | Entrant identity, seeded placement, reference-agent corpus, benchmarking, scheduler, Ruleset registry | `docs/RULES_V4.md` names several of these modules directly by dotted path |

3. **One outright false claim, not just staleness (lines 837–839):** the document states two
   Designer defects were fixed "not the history UI itself, which is deferred." This is false
   today — `app/views/evaluation_history.py` (1,481 lines) implements `EvaluationHistoryDialog`
   and is fully wired into the Designer (`app/agent_designer.py:92,285,912`). It shipped in the
   V5 era; this sentence was never revisited.
4. **Body sections that ARE present were spot-checked and found accurate**: module
   existence/layering (lines 27–50), `NativeMatchService`/`match_service.py` (lines 52–101),
   `process_runtime.py` (lines 103–107, matches `docs/RULES_V4.md`'s independent description),
   `battle2.*` schema-identifier usage (correctly NOT flagged as rebrand drift — `AGENTS.md:
   116-118` sanctions this permanently), dependency-direction diagrams (lines 355–404), and the
   `app/agent_designer.py`/`app/replay_viewer.py` entry-point description (lines 247–286).
5. **The `PygameCanvas` claim (lines 200–206) is the one confirmed-stale item that is not a
   coverage gap but a fully reversed fact** — see §1 and §6.1.

Recommended correction scope for Phase 2 (not performed here): (a) rewrite the header/version
claim — mechanical; (b) add subsections for the six module groups in the table above, in the
same style as the existing `NativeMatchService` section — the substantial part of the work; (c)
correct the false evaluation-history sentence; (d) decide the fate of lines 427–932 (see §5.4).

### 5.4 Cleanest pure-extraction candidate: `ARCHITECTURE.md` lines 427–932

Roughly half the document (~500 of 931 lines) is a "v0.4.0 through v0.8.0 delivery history"
section. This content is fully redundant with `CHANGELOG.md`'s own `[0.4.0]` through `[0.8.0]`
entries (confirmed present at `CHANGELOG.md` lines 1855–2278) and with git tags `v0.4.0`
through `v0.8.1`. This is a strong EXTRACT candidate — moving it out of the *current
architecture* document and into `docs/archive/` (or dropping it in favor of `CHANGELOG.md` +
tags outright) would also shrink the document that's supposed to describe current architecture
back toward actually doing that, independent of the coverage-gap fix in §5.3.

### 5.5 Other specific findings

- **`docs/COMPATIBILITY.md`, `docs/RULES_V4.md`, `docs/FUTURE_PLANS.md`** (with one flagged gap
  below), **`CHANGELOG.md`, `README.md`** are all current, actively and incrementally
  maintained, and should remain authoritative KEEPs. `COMPATIBILITY.md` in particular shows the
  release-by-release incremental-extension pattern `ARCHITECTURE.md` should have followed and
  didn't.
- **`docs/FUTURE_PLANS.md` gap**: its "Multiple execution processes / multipronged agents"
  research item (lines 282–303) describes substantially what shipped Ruleset v4 already does
  (`docs/RULES_V4.md:28-39`'s multi-process-per-entrant model), but the document was never
  updated to note this — flagged **INVESTIGATE** since v4's undifferentiated processes may only
  partially satisfy the original research question, not a clear "delete this item" call. Its
  companion "Future rulesets" section (lines 410–433) also stops one ruleset short of current
  reality.
- **`docs/specs/*.md` reclassification** is an open, non-urgent question: all 16 specs describe
  now-fully-shipped features and are still actively cross-referenced by `ARCHITECTURE.md` and
  `RULES_V4.md`/`COMPATIBILITY.md` as the authoritative design record for that behavior — they
  function as permanent reference documentation now, not "specs awaiting implementation," even
  though `CLAUDE.md`/`AGENTS.md` frame the directory as pre-implementation. **INVESTIGATE**,
  framing question only, not a content problem.
- **Terminology drift in specs**: `docs/specs/agent_designer_workflow.md`, `agent_scaffold.md`,
  `agent_test.md`, `agent_lab.md`, and `evaluation_history.md` retain pre-v1.4 binary names
  (`battle-agent-designer.exe`, `battle-replay-viewer.exe`, `battle-cli`) that `AGENTS.md:
  111-114` says were retired. Low-risk find/replace, but real drift, in files still cited as
  authoritative.

---

## 6. Source and dead-code audit

### 6.1 `pygame_canvas.py` — corrected finding

As established in §1: the file does not exist (deleted in `468028c`, before `v1.4.0`). No
Python module needs to be deleted. The remaining work is exclusively a documentation
correction across the five live files that still describe it as present-tense unremoved code:
`ARCHITECTURE.md:200-206`, `docs/MANUAL_SMOKE_TESTS.md:74-78` (which even instructs "remove
this note once `PygameCanvas` is either wired into a consumer or removed" — it was removed, and
the note was never removed as its own text instructs), `docs/specs/agent_designer_workflow.md`
(4 locations), `docs/specs/agent_lab.md`, and `docs/research/v6/V6_PHASE0_BASELINE.md:232,293`
(this program's own Phase 0 charter). `docs/archive/v1/V1_4_PLATFORM_INTEGRITY.md:42`, by
contrast, is correctly framed — it describes the removal as a past historical event and is not
flagged.

### 6.2 `_legacy/` — confirmed isolated, KEEP as-is

`pytest.ini` sets `pythonpath = _legacy` and includes `_legacy/tests` in `testpaths`, which is
what lets `_legacy/tests/test_smoke.py` resolve its bare `from core import Config, Kernel`
import against `_legacy/core.py`. A repo-wide check for any *other* bare `import
core|agents|main|renderers` that could accidentally resolve against that same pythonpath entry
found zero hits — only `test_smoke.py` uses it. `pyproject.toml`'s ruff `extend-exclude` lists
`_legacy/{core,agents,main,renderers}.py` and `agents_tooling/` by name, but **deliberately not
`_legacy/tests/`**, confirming `AGENTS.md`'s claim that the characterization suite itself stays
linted. The two `test_smoke.py` tests (`test_ticks_progress`, `test_single_agent_early_stop`)
assert only that the frozen `Kernel`/`Config` still imports and runs at all — proportionate
scope for a frozen fixture's existence check, not vestigial, not expandable without scope creep.
One real cross-reference exists: `tournament/roster.json` points two "custom" warrior entries at
`_legacy/agents_tooling/*.asm` (§6.5). **KEEP.**

### 6.3 Compatibility adapters beyond `battle_engine.core`

`engine/src/battle_engine/evaluation_history/{v1_adapter,v2_adapter,behavior_adapter,
group_adapter}.py` are the only adapter/shim-pattern modules found outside the deliberately-kept
`battle_engine.core` facade. All four are live, wired into both `evaluation_history/
discovery.py` and (for `behavior_adapter`/`group_adapter`) directly into the Agent Designer GUI
(`app/services/evaluation_history_workflows.py:57-58`). These are **not** a closed migration
window — they are the permanent read layer for historical `bytefray.evaluation` schema
generations, and remain required for as long as any user might hold a historical artifact of
that generation. **KEEP all four**, consistent with Phase 0's existing `v2_adapter.py` KEEP.

### 6.4 Dead GUI paths, obsolete wrappers, stale flags, duplication — all negative results

Each of these was investigated with the same rigor as the positive findings, and all returned
clean:

- **Dead GUI paths in `app/`**: traced reachability from `app/agent_designer.py` — all 9 view
  modules, all 6 widget modules, and all service modules are either directly imported or
  transitively reachable. Zero unreachable modules found.
- **Obsolete command wrappers / retired names**: every `battle2\b|battle-cli|battle_cli\b` hit
  (~35, grepped across `engine/src`, `client/src`, `app`) is a `battle2.result`/`battle2.replay`/
  `battle2.tournament` schema-identifier string — exactly the class `AGENTS.md:115-119` sanctions
  as permanently retained. No executable command, CLI subcommand, or entry point named
  `battle2`/`battle-cli`/`battle-*` exists in current code. `pyproject.toml [project.scripts]`
  declares only the 4 current commands.
- **Stale feature flags**: the complete env-var inventory (`BYTEFRAY_AGENTS_JSON`,
  `BYTEFRAY_AGENTS_DIR`, `BYTEFRAY_GUI_SMOKE_EXIT_MS`, `PMARS_CMD`, plus standard platform vars)
  contains no "graduated to stable but never removed" or "nothing sets this anymore" pattern.
  Zero `# TODO`/`# FIXME`/`# deprecated`/`# temporary` markers exist anywhere in `engine/src`,
  `client/src`, or `app`.
- **Duplicated implementations**: the one known historical duplication (`sdk/`, a byte-identical
  copy of `_legacy/agents_tooling/`, plus a duplicate `hunter_feedback_bundle` sibling) is
  already remediated — `sdk/` does not exist on disk (`docs/PROJECT_HISTORY.md:34-39` documents
  the cleanup). No new duplication was found.
- **Transitional migration code**: all 4 "migrat"-matching hits across `engine/`, `client/`,
  `app/` describe either a completed-long-ago migration that became the permanent shape
  (`match_service.py:239-240`'s `as_legacy_statistics()` — misleadingly named, but the single
  canonical, currently-read builder of every result's statistics dict) or a comment explaining
  why a migration *isn't* needed (the Replay History SQLite cache is fully rebuildable). No
  closed-window migration code needing removal was found.
- **Ruleset-specific dead code**: confirmed structurally, not just by absence-of-evidence — the
  three narrower historical identities (`bytefray-rules-2-alpha1`, `-alpha11`, `-3-alpha1`) are
  explicitly documented in `ruleset_policy.py`'s own comments as "reusing the exact same shared
  implementation, not a subclass or a copy" (except `-3-alpha1`'s locality block, §4.3). No
  Python module exists whose only reason to exist is executing one specific one of these
  identities.
- **`agent_evaluation.py` (5,467 LOC)**: mapped its generation-dispatch structure in full. There
  is no separable "v1-only" chunk — v1 pairwise evaluation is the shared foundation
  (`EvaluationRequest`, `build_matrix`, `EvaluationService`) that v2/v4/group features are
  additively layered on top of, not an alternative to. Per the charter's explicit instruction,
  no split is proposed; this confirms the file should be left alone in this phase and the next.

### 6.5 Newly-characterized top-level trees not covered by Phase 0

Four top-level tracked trees were found during this session that Phase 0's directory map did
not enumerate at all:

- **`pmars/windows/`** (7 files) — **KEEP, live**. `engine/src/battle_engine/pmars.py`'s
  `_candidate_directories()` explicitly searches this literal path on Windows before falling
  back to PATH; exercised by `engine/tests/test_pmars.py`; `tools/bytefray.spec` and
  `tools/bytefray_cli.spec` both bundle `pmars.exe`+`COPYING` into the Windows installer
  (confirmed — this is a materially different claim from "excluded from the wheel," which is
  also true and not in conflict: `tools/check_wheel.py` asserts no `pmars` string appears in
  wheel contents except the `battle_engine/pmars.py` launcher module itself). **However**,
  `pmars-server.exe`, `AUTHORS`, `ChangeLog`, `CONTRIB`, and `README` inside this same directory
  are tracked but referenced by **nothing** — not bundled by any spec, not in the wheel, not
  used by any test. **DELETE candidate** for these 5 files specifically (§9, Batch D); `pmars.exe`
  and `COPYING` (the GPL notice) must stay.
- **`warriors/*.red`** (8 files) — **INVESTIGATE, likely DELETE or document-and-keep**. No test,
  CI job, or doc references this directory by path (the same-named `validate.red` used by
  `.github/workflows/linux-pmars-build.yml` comes from the *downloaded upstream pMARS source
  archive*, not this directory — a coincidental naming collision, confirmed by reading the
  workflow). These are legitimate, well-known Core War warriors (not junk), but currently
  undocumented, untested dead weight from a "why is this here" standpoint. A `pyproject.toml`
  comment (line 126) shows an abandoned, never-activated intent to package them.
- **`tournament/`** (root-level; distinct from the live `bytefray tournament` CLI feature backed
  by `TournamentService`) — **INVESTIGATE, human policy call**. `docs/TOURNAMENTS.md:97-98`
  already documents this directory as legacy ("the CLI... does not use
  `tournament/scripts/btctl.py`... remains a legacy standalone workflow and is not the supported
  execution path"). It is still directly unit-tested (`engine/tests/test_tournament_btctl.py`),
  and that test suite's assertions about `btctl.py`'s constructed CLI invocation do genuinely
  match today's live CLI flags — but `btctl.py`'s own `_find_build_sh()` cannot find a
  `build.sh` anywhere in the tracked tree. Commit `6feb10b` ("remove `sdk/`...") explicitly
  removed `sdk/`'s real, on-disk `build.sh` and updated the test to mock around its absence,
  without restoring the runtime capability — so every non-`report` `btctl.py` subcommand now
  fails immediately with `FileNotFoundError` for anyone without a private `build.sh`. The `.sh`
  wrapper scripts (`cla-vs-cgpt.sh`, `round_robin.sh`) are separately, doubly stale — they
  invoke a root-level `python3 main.py` that has not existed since the `engine/src` restructuring,
  with flags that predate the current CLI surface. **This is real, once-functional tooling that
  has silently bit-rotted, whose test suite was patched to hide the regression rather than catch
  it — retire it and its test together, or restore `build.sh` and make it whole. Either is a
  legitimate outcome; leaving it as-is (tested-but-broken) is the one option this audit does not
  recommend.**
- **`prompts/`** (2 files) — **KEEP, documented**. `CONTRIBUTING.md:151-160` names this directory
  explicitly as supporting tooling for the optional AI-assisted spec→issue→prompt→PR workflow.
  Not a diet candidate.

### 6.6 Root utility scripts

| Script | Documented? | Disposition |
|---|---|---|
| `sync_win.ps1` / `sync_win.cmd` | Yes — `CONTRIBUTING.md:35-39` names it explicitly as an optional convenience, and it was actively rewritten alongside the `sdk/` removal commit | **KEEP** |
| `pull.sh` | No — zero references in any doc, CI workflow, or CONTRIBUTING.md | **INVESTIGATE** (maintainer call — generic git convenience, superseded in function by `sync_win.ps1`) |
| `git-clean-branches.sh` | No — same as above | **INVESTIGATE** (maintainer call — generic, project-agnostic branch-hygiene tool with no Bytefray-specific logic) |

---

## 7. Test-suite archaeology

### 7.1 Corrected baseline

See §2 — the canonical counts going forward are **143** `engine/tests/*.py` files (62,656 LOC),
**16** `client/tests/*.py` files (9,109 LOC), **1** `_legacy/tests/*.py` file (17 LOC); **160**
files, **2,992** `def test_` function definitions (lower than the 3,709 *collected* test count
purely due to `@pytest.mark.parametrize` expansion — confirmed as parametrization, not missing
files, since HEAD matches Phase 0's starting SHA plus only documentation commits).

### 7.2 Classification summary

| Category | Files | Approx. test funcs | Meaning |
|---|---:|---:|---|
| CURRENT-PRODUCT (pure) | 126 | ~2,563 | Protects live, current-default behavior |
| CURRENT-PRODUCT + HISTORICAL-RULESET (dual) | 8 | 84 | Protects a still-selectable frozen identity (v1, v2, v4-alpha1, v4-alpha2) alongside shared current-product dispatch |
| HISTORICAL-RULESET (pure) | 10 | 201 | The narrow closed identities: 2-alpha1, 2-alpha11, 3-alpha1 |
| CURRENT-PRODUCT + COMPAT-PATH (dual) | 4 | ~61 | A live feature with an old-format read-back requirement |
| DEAD-FEATURE / closed-research-tooling candidate | 10 | 79 | Standalone research scripts with zero product callers, each with its own dedicated test file |
| STALE-DOCS-EXAMPLE / non-exercising | 1 | 2 | See §7.5 |
| Frozen pre-product fixture (sui generis) | 1 | 2 | `_legacy/tests/test_smoke.py` |
| **Total** | **160** | **2,992** | |

**Two clean negative results** worth stating explicitly: no DEAD-FEATURE tests exist for any GUI
or renderer component (in particular, zero test coverage of any kind references `PygameCanvas`/
`pygame_canvas` — consistent with §6.1's finding that the file simply doesn't exist), and no
accidental DUPLICATE-COVERAGE pairs were found. The closest look-alike pattern — alpha-vs-stable
"mirrored fixture" test pairs, e.g. `test_ruleset_v2_alpha11.py` vs. `test_ruleset_v2.py` — is
explicitly, deliberately documented promotion-mirroring backed by its own equivalence corpus
(§7.3), not redundancy to prune.

### 7.3 Golden/equivalence corpora — confirmed load-bearing KEEPs

Four files are release-blocking regression protection, not archaeology, and must not be touched
regardless of any ruleset disposition decision: `test_v4_stable_ruleset_equivalence.py` (proves
`bytefray-rules-4` and `-alpha2` are byte-for-byte identical apart from identity fields),
`test_ruleset_v1_equivalence.py` (pins Ruleset-v1 outcomes across the v1.4 ownership-accounting
optimization), `test_ruleset_v2_promotion_equivalence.py` (proves `-alpha11` and permanent v2
are semantically identical — this is the proof, not just a test, that v2's promotion was safe),
and `test_v4_trace_equivalence.py` (trace-schema v1-vs-v2-reader compatibility).

### 7.4 Cross-reference: tests tied to the three narrow historical ruleset identities

For Phase 2 to retire ruleset and test together if `bytefray-rules-3-alpha1` (or, less likely
given §4.3, one of the shared-implementation identities) is ever removed, the full reference
list matters — but so does an important caveat the test audit surfaced: many of the "reference"
hits are a single negative-assertion line (e.g., "assert this ID does NOT appear in `--help`
output," protecting current CLI hygiene) or one row in a cross-ruleset parametrized fixture
table, not a file whose whole purpose is that ruleset. Only files marked below as **defining**
would be deleted wholesale if a ruleset were retired; the rest need a one-line edit at most.

- **`bytefray-rules-2-alpha1`** (19 referencing files) — defining: `test_ruleset_v2_alpha1.py`,
  `test_v2_alpha1_reference_agents.py`.
- **`bytefray-rules-2-alpha11`** (10 referencing files) — defining: `test_ruleset_v2_alpha11.py`.
- **`bytefray-rules-3-alpha1`** (10 referencing files) — defining: `test_v3_phase2_locality_agents.py`,
  `test_v3_phase2_locality_evaluation.py`, `test_v3_phase2_locality_runtime.py` (41+ test
  functions combined). These three are the concrete test-removal cost if the ruleset itself
  (not the separate closed-research-tooling cluster, §7.6) is ever extracted.

Since §4.3 recommends KEEP for `-2-alpha1`/`-2-alpha11` (no separable engine code exists to
justify the churn), the only *live* deletion-cost question here is for `-3-alpha1`'s three
defining files, contingent on the still-open EXTRACT-ARCHIVE investigation in §4.3.

### 7.5 One dead test file with zero real assertions

`engine/tests/test_v4_stage6_observation.py` (71 lines, 2 test functions) is a design-exploration
scratchpad for a candidate Agent-API-v2 observation contract that predates and was superseded by
the real shipped `ObservationV2`. Both test functions assert purely against local hardcoded
variables (e.g., `action_applied = True` followed by `assert action_applied == True` three
lines later) and never call into `battle_engine` at all. It provides zero actual coverage today.
**INVESTIGATE → likely DELETE**: confirm the real `ObservationV2` contract (exercised properly
elsewhere, e.g. `test_v4_spectator_perspective.py`) supersedes what this file was exploring, then
remove it with no coverage loss.

### 7.6 Closed-research-tooling test cluster (distinct from the ruleset-3 test files above)

Ten test files exercise standalone research scripts under `tools/` that have **zero** callers
from any product, CLI, or app path (confirmed via `git grep` for `from tools\.`/`import tools\.`
outside `tools/`/`tests/` — zero hits):

| Research script(s) | Test file(s) | Test funcs |
|---|---|---|
| `tools/v3_closeout_defensive_timer.py`, `tools/v3_closeout_turtle_probe.py` | `test_v3_closeout.py` | 8 |
| `tools/v3_phase3_rescore.py` | `test_v3_phase3_rescore.py` | 7 |
| `tools/v3_phase6_defense_episode.py` | `test_v3_phase6_defense_episode.py` | 15 |
| `tools/v3_phase7_confound_isolation.py` | `test_v3_phase7_confound_isolation.py` | 7 |
| `tools/research/v5/*` (analyzer, corpus_runner, r3/r4 agent populations) | `test_v5_research_analyzer.py`, `_r1_metrics.py`, `_r3_agents.py`, `_r3_metrics.py`, `_r4_agents.py`, `_r4_population.py` | 42 |

`docs/archive/v3/V3_RESEARCH_CLOSEOUT.md` already reports the empirical results these v3 tools
produced — their job is done and recorded. **One caveat before wholesale removal**:
`engine/src/battle_engine/benchmarks.py` (344 LOC) is used by several of these research scripts
*and* by one CURRENT-PRODUCT test file, `test_default_python_agents.py` — so `benchmarks.py`
itself is **not** a clean orphan even though its research-script callers are. **INVESTIGATE**:
confirm `test_default_python_agents.py`'s dependency on `benchmarks.py` before treating that
module as removable alongside its research-script callers.

### 7.7 Largest test modules — all confirmed current-product, no archaeology found

The five largest test files (`test_replay_history.py`, `test_agent_package.py`,
`test_agent_evaluation_v2.py`, `test_v4_spectator_derivation.py`, `test_evaluation_history.py`)
were each individually confirmed to be current-product characterization suites with no
meaningful archaeological sub-section (the one COMPAT-PATH portion, `test_evaluation_history.py`'s
`adapt_v1` coverage, is a live compatibility requirement, not archaeology).

---

## 8. Agent/example/runtime-state audit

### 8.1 `engine/src/battle_engine/data/` — authoritative source inventory

| Directory | Count | Category |
|---|---:|---|
| `starter_agents/` | 21 (see §2's count-definition note) | Shipped starting points, installed to every user's writable catalog by `ensure_starter_agents()` |
| `reference_agents/` | 4 | Permanent test/reference infrastructure for the still-live Ruleset v2 vulnerable-core family — deliberately excluded from `STARTER_AGENT_NAMES`, **not** a legacy leftover |
| `v3_locality_agents/` | 6 | Closed-research fixtures for `bytefray-rules-3-alpha1`, still exercised by 3 defining test files |
| `v3_closeout_agents/`, `v3_phase7_agents/` | 1 + 1 | Closed-research fixtures for the standalone research-tooling cluster (§7.6) |
| `agent_template*` (4 dirs) | 4 | Designer "New Agent" scaffold templates — a distinct product surface from starter agents |
| `benchmarks/*.json` | 7 files | Frozen, content-addressed benchmark population data; "must never be edited" per `starters.py:24-28` |

**A packaging consequence of this classification**: `pyproject.toml`'s package-data glob
(`battle_engine = ["data/**/*"]`) sweeps `v3_locality_agents/`, `v3_closeout_agents/`, and
`v3_phase7_agents/` into every shipped wheel and installer, even though their only live
consumer is the test suite (and, for the locality set, the still-open ruleset-3
INVESTIGATE item). **This is a concrete, evidenced Phase 2 candidate**: exclude these three
directories from package-data while keeping them tracked in git for test use — a packaging
change, not a deletion, and one that needs no ruleset decision to be made first.

### 8.2 Starter-agent bootstrap mechanism — deterministic, but with a located fragility

`starters.py`'s `ensure_starter_agents()` is content-hash-driven (SHA-256 over LF-normalized
file content) and correctly implements a four-way classification: absent → full install;
already-current → no-op; untouched copy of a known-superseded past release → non-destructive
upgrade (including removing files the new release dropped); anything else → treated as
user-modified, only missing files restored, nothing overwritten. This is deterministic and
correctly distinguishes "safe to add" from "never touch user content."

**The fragility Phase 0 encountered has a located, concrete mechanism, found this session**:
`engine/tests/test_v4_stable_ruleset_equivalence.py:58-83`'s `_bootstrap_agent()` helper checks
`STARTER_SOURCE_DIRS = (REPO_ROOT / "agents", REPO_ROOT / ".../starter_agents")` **in that
order**, and its loop condition is `if source.is_dir(): shutil.copytree(...)` — it verifies only
that the directory exists, never that it actually contains `agent.py`/`agent.yaml`. This is
invoked for exactly `v4_claimer`, `v4_scout`, `v4_local_defender`, `v4_defender_scout`,
`v4_concentrated_attacker` — the same five names Phase 0 found emptied-but-present (stale
`__pycache__` only) in the real repo-root `agents/` catalog on this machine. Because the
writable runtime catalog is checked *before* the canonical bundled source, a stale/empty real
`agents/<name>` satisfies `.is_dir()` and silently shadows the correct fallback, copying
near-empty content and causing exactly the downstream `resolve_agent()`/match-setup failures
Phase 0 observed. (`v4_quorum`, reported *entirely absent* rather than empty, correctly falls
through to the bundled source under this same code — consistent with it not being one of the
five that failed.) This is recorded as evidence for Phase 2/3, not fixed here, per the charter's
explicit instruction not to redesign this mechanism in Phase 1.

### 8.3 The 5 tracked dev-fixture agents inside gitignored `/agents/`

`Nemesis`, `hydra`, `hydra_alpha2`, `nemesis_alpha2`, `viper` are tracked despite `/agents/`
being otherwise gitignored, via plain git semantics (a file tracked before a directory is
ignored stays tracked — no `.gitattributes` negation exists). The `.gitignore` comment
documenting this ("Existing tracked historical/reproducibility fixtures remain tracked") was
added deliberately during a prior V5 cleanup pass (commit `75f5a2d`, 2026-09-10) — **this was a
considered decision, not an oversight, and Phase 2 should not re-litigate it without new
information.** These five are the fixed historical opponent roster required, byte-for-byte, by
`test_v4_stable_ruleset_equivalence.py` (the release-blocking equivalence gate, §7.3) and
`tools/v4_alpha2_ecology_study.py`'s reproducibility requirements. No duplication exists between
these five and anything under `engine/src/battle_engine/data/`. **KEEP.**

### 8.4 Documentation-of-boundaries gap (not a cleanup item, a clarity item for Phase 3)

The distinctions between authoritative source, generated/installed copies, and content expected
to live outside git are each individually well-documented in-code (`.gitignore`'s comment,
`starters.py`'s module docstring, `reference_agents.py`'s docstring, `docs/TOURNAMENTS.md`), but
no single document assembles the full taxonomy. A new contributor would need to read four
separate files to reconstruct the picture this section assembles. Flagged for Phase 3
(architecture/context-locality), not a Phase 2 cleanup action.

---

## 9. Asset audit

| Asset | Size | Referenced by | Disposition |
|---|---:|---|---|
| `assets/branding/bytefray-logo-horizontal.png` | 190 KB | `README.md:4` | KEEP |
| `assets/branding/bytefray-icon.png` + `app/assets/branding/bytefray-icon.png` (byte-identical) | 145 KB ×2 | Runtime branding lookup (source checkout) + `pyproject.toml` package-data (wheel/frozen builds) | KEEP — deliberate, documented, tested duplication (two different consumers) |
| `assets/branding/bytefray-icon.ico` | 135 KB | All 4 `tools/*.spec` files (PyInstaller exe icon), `tools/installer.iss:26` | KEEP |
| `assets/branding/bytefray-brand-sheet.png` | **1.17 MB** | **No functional/code reference found anywhere** | **DELETE candidate.** A prior audit (`docs/research/v5/V5_ALPHA1_POST_RELEASE_HARDENING_AUDIT.md:369-372`) only investigated and rejected a *crash* hypothesis involving this file ("Verdict: REJECTED. No runtime code references `bytefray-brand-sheet.png`") — it never evaluated the file as repo weight, and never removed it. This audit re-confirms zero references and treats it as an open, undecided candidate — the single largest unreferenced tracked file found in the repository. |
| `docs/screenshots/v5-replay-showcase.gif`, `v5-agent-designer.png`, `v4-replay-broadcast.png` | ~150 KB combined | `README.md:15,47,367` | KEEP |
| `docs/screenshots/v3-*/` (~27 files, ~2 MB) | | Only referenced from **archived** v3 phase docs and one generic `docs/ROADMAP.md:166` pointer | Historical illustrations for closed v3 phases — candidate to move alongside the v3 archive content if/when it's reorganized, not a standalone deletion |

**A previously-flagged packaging asymmetry is already fixed, not still open**: the same V5 audit
above ("FIND-06 Asset Packaging Asymmetry") found `tools/agent_designer.spec` and
`tools/replay_viewer.spec` used to bundle the entire repo-root `assets/` directory (including
the 1.17 MB brand sheet) into every frozen GUI build. Current code (`tools/agent_designer.spec:
47-54`, `tools/replay_viewer.spec:25-32`) bundles only `app/assets/branding` (the single 145 KB
icon), with an explicit comment noting the full `assets/` directory is deliberately excluded.
Phase 2 should confirm this is reflected as closed in any tracker referencing FIND-06, but the
packaging code itself needs no further action.

**No large generated/binary fixture blobs were found tracked under `engine/tests/` or
`client/tests/`** — the largest tracked files there are all hand-authored `.py` test source,
consistent with this codebase's dense test-writing style, not accidentally-committed data.

**The `.pyc`-file claim raised by one sub-audit was independently checked and found false** —
see §3. No tracked `.pyc` file exists anywhere in this repository.

---

## 10. Packaging and configuration audit

`pyproject.toml`, `MANIFEST.in`, `.gitignore`, `pytest.ini`, all four `tools/*.spec` files,
`tools/build_win.ps1`, `tools/installer.iss`, `tools/check_wheel.py`, and all four
`.github/workflows/*.yml` files were each read in full. The overall result is clean: no stale
version-specific config, no undocumented lint-rule ignores, no orphaned PyInstaller spec, and no
`mypy.ini`/`setup.cfg`/`.ruff.toml` config drift (none of those files exist — all config is
correctly consolidated in `pyproject.toml`/`pytest.ini`).

Specific findings:

- **`pyproject.toml`**: package discovery (`packages.find`, `include = ["battle_engine*",
  "battle_client*", "app*"]`) correctly and structurally excludes `_legacy/`, `tournament/`,
  `warriors/`, `prompts/`, `pmars/` from ever being packaged — these trees' disposition is
  purely a tracked-files question, never a packaging-safety one. Every ruff ignore and mypy path
  entry carries an inline justification comment. One commented-out `[tool.setuptools.data-files]`
  example (lines 122–127) is a self-labeled illustrative comment, not decayed residue. No
  TODO/FIXME anywhere in the file.
- **PyInstaller specs confirm the pMARS distribution asymmetry is intentional, not an
  oversight**: `tools/pmars/README.md` states outright that this tooling "builds, but does not
  download, install, package, or redistribute, pMARS" and that "Bytefray does not currently
  distribute a Linux pMARS executable." Linux gets a checksum-pinned, build-at-CI-time upstream
  download (`.github/workflows/linux-pmars-build.yml`, which explicitly "uploads and retains no
  pMARS source or executable artifact"); Windows gets the one committed-binary exception because
  there's no equivalent "verified download, build locally" story for end users without an MSVC
  toolchain. This is a real, load-bearing product decision — not something to flatten for
  consistency's own sake, though Phase 3 could ask whether Windows could someday get the same
  treatment.
- **`docs/specs/run_match_pmars.md` is stale relative to the shipped implementation**: it
  documents a module path `engine/src/battle_engine/backends/pmars.py` with function
  `run_match_pmars(...)` that doesn't exist; the real module is `engine/src/battle_engine/
  pmars.py` with `run_pmars(...)` and a different public surface. This looks like a
  pre-implementation spec whose design changed during implementation and was never reconciled —
  a doc fix, not a code concern.
- **`linux-package.yml`** is push-triggered on `branches: [v4-rc2-development]` — a branch that
  still exists but has had no pushes in a long time, since development moved through v5.0.0 to
  `v6-research`. It still fires on `pull_request` and manual `workflow_dispatch`, so it isn't
  fully inert, but the push-branch pin is clear, unremediated V4-era CI residue.
- **Cross-reference for Phase 2 safety** (does any DELETE candidate silently break packaging?):
  confirmed **no** for `pygame_canvas.py` (doesn't exist), `pmars-server.exe`+unbundled pmars
  docs, and `warriors/` (none appear in `MANIFEST.in`, package-data, or any spec's
  `datas`/`hiddenimports`). The one real cross-reference to watch is `_legacy/agents_tooling/
  *.asm`, which `tournament/roster.json` reads by path — itself already a legacy, doc-flagged
  artifact (§6.5), so this dependency chain (`tournament/` → `_legacy/agents_tooling/`) should
  be resolved as one unit if either side is ever retired, not independently.

---

## 11. Dependency-grouped cleanup candidates

Grouped into coherent units, per the charter's instruction to avoid hundreds of isolated
file-level recommendations. Each names its constituent files/tests/docs and its dependencies on
other groups.

| Batch | Contents | Depends on / must coordinate with |
|---|---|---|
| **A — Archive closed v4/v5 research** | Relocate `docs/research/v4/` (31 files) → `docs/archive/v4/`, `docs/research/v5/` (48 files) → `docs/archive/v5/` (new directory), following the exact precedent of `docs/archive/v4/DOCUMENTATION_INVENTORY.md`'s prior v1/v2/v3 pass | Must update the live cross-references in `ARCHITECTURE.md:244`, `RULES_V4.md`, `V4_ALPHA1_DESIGN.md`/`V4_ALPHA2_DESIGN.md`, `docs/COMPATIBILITY.md` that link into these directories by relative path. Independent of every other batch. |
| **B — `ARCHITECTURE.md` correction pass** | Fix stale header; add the 6 missing module-group subsections (§5.3); correct the false evaluation-history-deferred claim; extract or drop the redundant v0.4–v0.8 delivery-history sections (§5.4) | Should happen alongside or after Batch A (the extracted delivery-history content is exactly the kind of material Batch A is relocating elsewhere) |
| **C — Stale `pygame_canvas.py` documentation correction** | Strike/correct the false present-tense claims in `ARCHITECTURE.md`, `docs/MANUAL_SMOKE_TESTS.md`, `docs/specs/agent_designer_workflow.md`, `docs/specs/agent_lab.md`, and (for future reference) note the correction against `V6_PHASE0_BASELINE.md` | Independent; can happen alongside Batch B since it touches `ARCHITECTURE.md` too |
| **D — Orphaned pMARS Windows sidecar files** | Delete `pmars/windows/{pmars-server.exe, AUTHORS, ChangeLog, CONTRIB, README}`; keep `pmars.exe` + `COPYING` | None — confirmed zero packaging/test/doc dependency (§6.5, §10) |
| **E — v3 closed-research packaging exclusion** | Exclude `v3_locality_agents/`, `v3_closeout_agents/`, `v3_phase7_agents/` from `pyproject.toml` package-data while keeping them tracked for test use | Independent of the ruleset-3 EXTRACT-ARCHIVE question (§4.3) — this is a wheel-content fix that needs no ruleset decision first |
| **F — Closed-research tooling + its tests** | `tools/v3_closeout_*.py`, `tools/v3_phase3_rescore.py`, `tools/v3_phase6_defense_episode.py`, `tools/v3_phase7_confound_isolation.py`, `tools/research/v5/*` + their 10 dedicated test files (79 test functions total) | **Blocked on confirming `engine/src/battle_engine/benchmarks.py`'s status** (§7.6) — `test_default_python_agents.py`, a CURRENT-PRODUCT test, also depends on it, so `benchmarks.py` itself is not part of this batch even if its research-script callers are removed |
| **G — `tournament/` + `warriors/` disposition** | Either (i) retire `tournament/{roster.json,rosters/,scripts/}` + `warriors/*.red` + `engine/tests/test_tournament_btctl.py` together, or (ii) restore `build.sh` and make the pipeline whole again | **Human policy decision required** (§13) — this audit does not recommend one outcome over the other, only that "tested but silently broken" is not acceptable as a standing state |
| **H — Ruleset-3 locality extraction** | `bytefray-rules-3-alpha1`'s mechanic block in `python_runtime.py`, `v3_locality_agents/` (6 dirs), 3 defining test files (41+ funcs), associated docs | Requires the coupling-boundary scoping work identified in §4.3 before any code moves; do not conflate with Batch F (different mechanism — ruleset engine code vs. standalone research scripts) |
| **I — Dead exploratory test** | Delete `engine/tests/test_v4_stage6_observation.py` after confirming `ObservationV2` supersedes it (§7.5) | None |
| **J — Root vestigial scripts** | `pull.sh`, `git-clean-branches.sh` | **Human policy decision** — maintainer call, not evidenced as unsafe to remove but also not evidenced as still needed |
| **K — Unreferenced brand asset** | `assets/branding/bytefray-brand-sheet.png` (1.17 MB) | None — confirmed zero references; a prior audit investigated only a crash hypothesis and never revisited this as repo weight |
| **L — CI/spec hygiene** | Update or remove `linux-package.yml`'s stale `v4-rc2-development` push-trigger branch; reconcile `docs/specs/run_match_pmars.md` with the actual `battle_engine/pmars.py` implementation; find/replace pre-v1.4 binary names in 5 spec files (§5.5) | None — all independent, low-risk doc/CI fixes |

---

## 12. Quantified reduction estimates

Baseline reference point: Phase 0's repository metrics (821 tracked files, 178,156 Python LOC,
206–207 Markdown files, 227 files under `docs/`), corrected per §2/§7.1 where Phase 0's own
arithmetic was inconsistent.

### 12.1 High-confidence reduction (strong evidence, no policy decision required)

| Item | Files | Approx. size |
|---|---:|---:|
| Batch D — orphaned pMARS sidecar files | 5 | ~276 KB (binaries + text) |
| Batch K — unreferenced brand asset | 1 | 1.17 MB |
| Batch I — dead exploratory test | 1 | 71 lines |
| Batch C — stale doc corrections (edits, not deletions) | 5 files edited | n/a (correction, not size reduction) |
| Batch E — packaging exclusion (wheel/installer size only; files stay tracked) | 16 dirs' worth of data excluded from package-data | Wheel/installer size reduction only — no git-tracked file count change |
| Batch L — CI/spec hygiene | 1 workflow + 1 spec + 5 files' worth of terminology fixed | n/a |
| **Total tracked-file reduction, high confidence** | **~6-7 files** | **~1.4 MB** |

This is deliberately a small number. The charter warned against inflating estimates, and the
evidence supports only a modest, low-risk first cut of genuinely orphaned material. The bulk of
this audit's value is not in file-count reduction but in the **Batch A documentation
relocation** (79 files, ~2.35 MB moved, not deleted, out of the active-research framing and into
archive) and in **correcting false claims** (pygame_canvas.py, the evaluation-history-deferred
sentence, Phase 0's own count errors) that would otherwise continue to mislead future phases.

### 12.2 Possible reduction (requires a policy decision — see §13)

| Item | Files | Approx. test-function reduction | Contingent on |
|---|---:|---:|---|
| Batch F — closed-research tooling + tests | ~15 tool/test files | 79 | Confirming `benchmarks.py` has no other product caller beyond `test_default_python_agents.py` (it does — so `benchmarks.py` itself stays either way) |
| Batch G — `tournament/` + `warriors/` retirement | ~17 files + 1 test file | Unknown (test_tournament_btctl.py func count not separately tallied) | Human policy: retire vs. restore |
| Batch H — Ruleset-3 extraction | 6 packaged agent dirs + `python_runtime.py`'s locality block (lines TBD) + 3 defining test files | 41+ | Coupling-boundary scoping (§4.3) — not yet safe to schedule for Phase 2 without that scoping work |
| Batch J — root vestigial scripts | 2 files | 0 | Maintainer call |

**Markdown consolidation** (Batch A) is a relocation of 79 files / ~2.35 MB, not a deletion —
it should not be counted toward either "reduction" total above, since the content survives (just
relocated), but it is the single highest-confidence, highest-value structural fix this audit
found, and is called out on its own for that reason.

### 12.3 What this audit explicitly does NOT recommend removing

Per §4 and §6.4: none of the 8 ruleset identities' execution code beyond the single open
`bytefray-rules-3-alpha1` locality-extraction question; none of the 4 `evaluation_history`
adapters; `_legacy/` in its entirety; `agent_evaluation.py` (no split, no removal); any GUI
view/widget/service in `app/`; any of the 5 tracked dev-fixture agents in `/agents/`. These were
each investigated as candidates and found, on evidence, to be load-bearing.

---

## 13. Human policy decisions requiring approval

These are not technical questions this audit can resolve on its own — each has real, named
consequences on both sides, spelled out here without a recommendation, per the charter's
instruction not to silently choose a compatibility policy because it makes deletion easier.

1. **`bytefray-rules-3-alpha1`: extract to an archival/research package, or keep in the live
   tree?** *Keeping it* costs nothing in product surface (it's already invisible to GUI/CLI) but
   keeps a self-contained, non-shared gameplay mechanic block in the main engine indefinitely.
   *Extracting it* would require the coupling-boundary scoping work in §4.3 and would need a
   minimal replay-classification shim to preserve historical-replay readability — real
   engineering work for a identity with zero current-user-facing exposure.
2. **`tournament/` (root-level legacy tooling): retire, or restore `build.sh` and make it
   whole?** *Retiring* removes a documented-legacy, currently-broken-for-most-users workflow
   and its test. *Restoring* it means recreating or relocating a `build.sh` this repository no
   longer ships (it depended on the now-removed `sdk/`). Leaving it as-is (tested but broken) is
   explicitly not recommended by this audit as a standing state, but which of the other two
   paths to take is a product-scope call, not a technical one.
3. **`warriors/*.red`: document a real use for the pMARS backend, or remove?** These are
   legitimate example content with no current test/CI/doc tie-in. Keeping them without
   documentation preserves optionality for a future pMARS how-to at zero present cost; removing
   them is equally costless today but forecloses that path without a rewrite.
4. **How far should replay/result execution compatibility extend, in principle, beyond what
   §4.2 already establishes?** This audit found that replay *reading* never depends on the live
   engine for any current ruleset — but that finding answers "is extraction structurally
   possible," not "should Bytefray promise historical rulesets stay executable (not just
   readable) indefinitely." That's a product commitment, not a source-code fact.
5. **Should `docs/specs/` be reframed from "pre-implementation" to "design reference," given
   that all 16 current specs describe shipped features and several are still cited as
   authoritative by live docs?** (§5.5) A naming/framing question with no code consequence
   either way, but it affects how future contributors are told to use the directory.
6. **`pull.sh` / `git-clean-branches.sh`: keep as undocumented personal convenience, formally
   document, or remove?** No evidence either way on whether the maintainer still uses these
   day-to-day; only the maintainer can answer that.
7. **Root utility script and CI residue** (`linux-package.yml`'s stale branch trigger): should
   Phase 2 simply fix it, or does it indicate other CI workflows deserve a fresh audit pass
   beyond what Phase 1 scoped?

---

## 14. Proposed Phase 2 cleanup batches

Restating §11 in execution order, grouped by risk and dependency rather than by audit section.
No implementation prompts are written here — only ordering and rationale, per the charter.

**Tier 1 — zero-policy-decision-required, safe to schedule immediately:**
1. Batch D (orphaned pMARS sidecar files)
2. Batch K (unreferenced brand asset) — pending a final human "yes, remove" since it's a
   judgment call about institutional-memory value even with zero technical references
3. Batch C (stale `pygame_canvas.py` doc corrections)
4. Batch L (CI/spec hygiene)
5. Batch E (v3 package-data exclusion)
6. Batch I (dead exploratory test), pending the one-line `ObservationV2` confirmation

**Tier 2 — structural, high-value, needs coordinated cross-reference updates but no policy
decision:**
7. Batch A (archive docs/research/v4+v5) — do this before or alongside Batch B, since Batch B's
   extracted `ARCHITECTURE.md` content is exactly the kind of material Batch A is relocating
8. Batch B (`ARCHITECTURE.md` correction pass)

**Tier 3 — needs a human policy decision from §13 before scheduling:**
9. Batch G (`tournament/`+`warriors/`)
10. Batch H (ruleset-3 extraction) — additionally blocked on coupling-boundary scoping even
    after a policy decision is made
11. Batch J (root scripts)

**Tier 4 — needs one more piece of technical confirmation before scheduling:**
12. Batch F (closed-research tooling) — confirm `benchmarks.py`'s status is unaffected before
    removing its research-script callers

---

## 15. Items deliberately deferred to Phase 3 (architecture / context-locality)

- `agent_evaluation.py`'s 5,467 LOC — confirmed in §6.4 to have no extractable dead section in
  Phase 1's terms, but its size remains the natural first candidate for a future
  context-locality/modularization pass, per Phase 0's own framing. Not touched here.
- The documentation-of-boundaries gap in §8.4 (no single document assembling the source vs.
  generated vs. outside-git taxonomy for agent directories) — a clarity/architecture concern,
  not a Phase 2 file-disposition action.
- Whether Windows pMARS distribution could someday match Linux's "verified download, build
  locally, never commit a binary" model (§10) — a build-architecture question, not a diet
  question.
- The eleven-file v4 Spectator research cluster's missing closeout/summary document (§5.2) — a
  synthesis-writing task, arguably a Phase 2 documentation task or a Phase 3 architecture-history
  task depending on how Phase 2 scopes Batch A; flagged here so it isn't lost either way.

---

## 16. Risks and unresolved questions

- **The core risk this audit surfaces about itself**: every finding here rests on grep, static
  read, and cross-agent corroboration — not on running the test suite (deliberately, per the
  charter's "optional if literally no executable/configuration code changed" instruction) or on
  executing any of the flagged research tooling to confirm it's truly uncalled. The
  `benchmarks.py`/`test_default_python_agents.py` finding in §7.6 is a concrete example of why
  this matters: a naive "zero product callers" grep for the research scripts would have missed
  that one of their dependencies is *also* used by current-product tests. Phase 2 should treat
  every "confirmed zero callers" claim in this report as "zero callers found by static search,"
  and re-verify with the same rigor before deleting.
- **This audit itself may contain errors it didn't catch.** §3 documents one sub-agent claim
  (tracked `.pyc` files) that was caught and nullified by a second independent check within this
  same phase. That the process caught one error is reassuring; it is not proof no others slipped
  through. Phase 2 should re-verify high-impact claims (especially any DELETE recommendation)
  against source before acting, exactly as this phase did to Phase 0's `pygame_canvas.py` claim.
- **`bytefray-rules-3-alpha1`'s coupling boundary is explicitly unresolved** (§4.3) — this is
  the one ruleset-disposition question this audit could not close, and Phase 2 must not treat
  "leaning EXTRACT-ARCHIVE" as equivalent to "safe to extract."
- **`tournament/`'s broken build pipeline is a live risk independent of this audit's
  recommendations**: anyone relying on it today (if anyone still does — unknown) is already
  experiencing `FileNotFoundError` on every non-`report` subcommand. This predates Phase 1 and
  is not caused by it, but is now formally on record.
- **No full test-suite rerun was performed for this phase**, consistent with the charter (no
  executable/configuration code changed). This means none of this report's claims about test
  behavior are re-validated by an actual pytest run in Phase 1 — they rest on static reading of
  test source, which is appropriate for a "what exists and what does it protect" audit but is
  not a substitute for Phase 2 running the suite before and after any actual change.

---

## 17. Final Phase 1 recommendation

Proceed to Phase 2 using the batch structure in §14, starting with Tier 1. Before any Tier 2+
batch, re-verify this report's specific claims for that batch against current source — not out
of distrust of this specific audit, but because that discipline is what caught this phase's own
two errors (§3's `.pyc` claim, and the far more consequential `pygame_canvas.py` claim inherited
from Phase 0) and should be treated as a standing practice for this program, not a one-time
correction.

The most important single output of this phase is not a deletion list — the high-confidence
deletions are modest (§12.1) — it is the demonstration that **claims about this repository's
dead weight need to be re-verified against source before being acted on, even when they come
from this program's own prior phase.** Phase 2 should carry that discipline forward at least as
rigorously as Phase 1 applied it here.

No files besides this report were modified during Phase 1. `main` was not touched. The working
tree was clean at the start of this phase and remains clean except for this new file at its
close (see verification below).

---

## Appendix: Phase 1 close-out verification

```
git status --porcelain          # only this report, as an untracked/new file, until committed
git diff --check                # to be run before any commit of this report
git log --oneline -3            # HEAD unchanged from ffcbe9f until this report is committed
```

Per the charter, this report is not committed as part of Phase 1 unless explicitly instructed.
