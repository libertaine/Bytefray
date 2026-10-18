# Component Identity and M2-5 Reconciliation — Merge and Qualification Report

**Date:** 2026-10-18
**Branch:** `v6-m2-5-identity-integration` (local, unpushed)
**Recommendation for Bytefray 5.1 Alpha Release Candidate Preparation: HOLD.**
The HOLD is narrow. The merge is clean and introduces no regression. One
defect inherited from the accepted Spectator integration can delete user files,
and it needs a separately authorized fix first (§9, §10).

Nothing was pushed, tagged or published, and no release branch exists. The
application version is still `5.0.0`, and no M2-6 or E9 activity occurred.

---

## 1. Commit identities

### Starting checkpoints (verified in local Git)

| Checkpoint | Commit | Tree | Where |
| --- | --- | --- | --- |
| Merge base: M2-4 | `10c3530f035335b89716d5bda7ce138440767a71` | `893ee89d…` | `origin/v6-research` (published) |
| M2-5 qualification | `bb6c4b88713a4a0552db3bf4a561b803b306b52b` | `b909d012…` | `v6-alpha1-m2-5-qualified` **and** `origin/v6-alpha1-m2-5-qualified` (published) |
| Spectator integration | `1ac0d27705b76e470cabca689b500bcf242d2630` | `ecd1f69f…` | `v6-spectator-integration` (local); an ancestor of `10da315` |
| Component identity | `10da3150b49f1f3fd91c8928d94f8dfb4884c91e` | `dddc2d73…` | `v6-component-identity` (local) |

### Final commits on the integration branch

| Commit | Tree | Content |
| --- | --- | --- |
| `22f092cd8e54d3cd74b9cedf3ef1379f2ec64c29` | `9041d70d49bba5055f4b2f87798ccf8622b7fd3e` | `git merge --no-ff bb6c4b8` onto `10da315`. Conflict-free; the tree equals the `git merge-tree` dry run. |
| `cbca3b60a1a41391bfcb2d76db9c0404227015dc` | `884c7e54262bc1c83fd110633aaebc889bd32120` | Documentation only (§6). |
| the commit adding this report | — | This file only. |

### Ancestry

```text
10c3530  M2-4 (origin/v6-research)
 |\
 | bb6c4b8  M2-5 qualified source (published; one commit)
 |  \
 b3c4e8e─9729fa6─33eb63c─d0dc955─1ac0d27       Spectator integration
  └─283b3ed─2bf4f74─c77771b─10da315             component identity
                                  \  \
                                  22f092c  merge (parents 10da315, bb6c4b8)
                                     |
                                  cbca3b6  docs: accepted M2-5, ROADMAP
                                     |
                                  (report)
```

`git merge-base --all 10da315 bb6c4b8` returns only `10c3530`. Neither line
was rebased or rewritten. Both parents' histories are preserved as they were,
including the published `bb6c4b8`.

## 2. Changed-file inventory

From `10c3530` to `cbca3b6`: 47 files, +8,019/−86. No binary file changed.

| Origin | Files |
| --- | --- |
| **M2-5 (`bb6c4b8`), 5** | `app/views/replay_history.py` (PD-1, 1 line), `tests/test_v5_replay_history_qualification.py` (fixture and 8 cases), new `docs/v6/V6_ALPHA_M2_5_PUBLIC_SUMMARY_01.md`, `…_SOURCE_MANIFEST_01.json`, `…_UBUNTU_CONFIRMATION_01.md` |
| **Identity line, engine (6)** | `agent_test.py`, `cli.py` and `command.py` (help text; `command.py` also adds the `bytefray spectator` dispatch); `launchers.py` (`build_spectator_command`); new `ruleset_names.py` |
| **Identity line, client (4)** | `sensing_presentation.py` and `renderers/sensing_renderer.py` (labels); new `spectator_export.py` and `tests/test_spectator_export.py` |
| **Identity line, Designer app (9)** | `agent_designer.py` (Spectator preference), `services/replay_history_presentation.py`, `services/ruleset_options.py`, `services/tournament_results.py`, `views/development.py`, `views/tournament.py`, `widgets/ruleset_combo.py` (labels); new `services/spectator_viewer.py`, `widgets/spectator_launch.py` |
| **Identity line, tests (11)** | engine `test_command.py`, `test_v5_replay_history_presentation.py`; new `test_component_identity.py`, `test_release_compatibility_record.py`, `test_spectator_viewer_service.py`; root `test_v5_alpha1_phase4_tournament_results.py`; new `conftest.py`, `test_agent_designer_spectator.py`, `test_designer_ruleset_display_names.py` |
| **Identity line, tools and docs (13)** | new `tools/release_compatibility.py`; `AGENTS.md`, `CHANGELOG.md`, `INSTALL.md`, `README.md`, `docs/AGENT_AUTHORING.md`, `docs/COMPATIBILITY.md`, `docs/ROADMAP.md`; new `docs/COMPONENT_VERSIONING.md`, `docs/COMPONENT_IDENTITY_TRANSITION_REPORT.md`, `docs/SPECTATOR_REMEDIATION_20261018.md`, `docs/specs/spectator_export.md`, the `docs/releases/BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.{json,md}` pair |
| **Docs commit `cbca3b6`** | new `docs/v6/V6_ALPHA_M2_5_CLOSURE_01.md`; edits to `README.md`, `docs/ROADMAP.md` and the compatibility record pair |

No path is changed by both lines.

## 3. Preservation and source-manifest assessment

All checks below are read-only, and their outputs are retained (§12).

| Check | Result |
| --- | --- |
| `delta(10da315 → 22f092c)` equals `delta(10c3530 → bb6c4b8)` | **true**: same blob IDs and modes |
| `delta(bb6c4b8 → 22f092c)` equals `delta(10c3530 → 10da315)` | **true** |
| Paths in the merge tree not taken from either parent's delta | **none**: no evil merge |
| M2-5 source manifest, 1,249 source/test identities, raw working bytes | **1,233 byte-identical**; **16 differ**, each byte-identical to the accepted identity line's file; 0 unexpected; 0 missing |
| M2-5 portable fixtures | **20/20** identical |
| PD-1 accepted bytes | `replay_history.py` `6994479d…`, fixture `b786ebcc…`: both identical |
| Manifest and Ubuntu handoff bytes | `dd2b5579…` and `a14ce2ba…`, matching the published-commit hashes recorded at the 2026-10-17 preflight |
| Protected paths: `docs/v6`, `docs/research`, `docs/archive`, `tools/research`, `engine/src/battle_engine/data`, `_legacy`, `agents`, `assets`, fixtures and goldens, `rules.py`, `ruleset_policy.py`, `match_service.py`, `sensing*.py`, `replay.py`, `result_model.py`, `agent_trace.py`, `agent_api.py`, `pyproject.toml`, `tools/installer.iss` | No pre-existing file changed. The only additions are the three published M2-5 documents and the new closure record. |
| Historical E9 pins (the M2-5H method) | Both v2 freeze manifests are byte-identical to the frozen baseline `b948540`; **329 pins, 0 mismatches** |
| Retained M2-5H Qualification Report 01 (untracked) | SHA-256 `e6513140…`, equal to the published `retained_report_sha256`; not committed or published |
| Application version | `pyproject.toml` `5.0.0`; `installer.iss` `AppVersion`/`ReleaseTag` `5.0.0` |
| E9 / Requirement C | ROADMAP statements unchanged: execution LOCKED, OPERATIONALLY BLOCKED, Requirement C NOT ESTABLISHED |
| Shared repository refs (before/after snapshot) | 190 → 191. The only addition is `refs/heads/v6-m2-5-identity-integration`; nothing changed or was removed. `refs/codex/*` stayed at 31; stashes unchanged |
| Pre-existing worktrees (HEAD, branch, porcelain status, index bytes) | All 16 unchanged, including `work/v6-m2-clean`, the M2-5 publication checkout, `component-identity`, `spectator-integration` and `m1_1_frozen_baseline`. The Spectator clone `14089a7` is unchanged |

**What the manifest result means.** M2-5's qualification binds to `bb6c4b8`.
The 16 superseded identities carry the identity line's own qualification
instead: the Spectator export command, Designer's Spectator launch path, and
presentation-only labels. The merged tree as a whole has the regression
evidence in §7. It is not a new M2-5 qualification.

## 4. Functional overlaps beyond the textual merge

| Overlap | Assessment |
| --- | --- |
| New `tests/conftest.py` autouse `BYTEFRAY_SPECTATOR=off`, and the M2-5 test module | The M2-5 module builds `ReplayHistoryWindow` directly, and its handoff test records the launcher. The calendar and handoff assertions are unchanged; merged and M2-5-parent runs both pass the same 36 nodes. Side effect: no Designer GUI test exercises an *installed* Spectator (§10). |
| `replay_history_presentation.py` label change, and PD-1 | Only `_readable_ruleset()` changed. `day_bounds()`, which the M2-5 test imports, and the PD-1 fallback are byte-unchanged in behavior. The 25-case date/calendar selection passes on the merged tree on Windows and Linux (§7). |
| Designer Spectator preference, and M2-5-qualified viewer handoffs | **Replay History → viewer is unchanged**: it still calls `open_pygame_client_direct` at `app/views/replay_history.py:1523`. Tournament and the Advanced replay browser also stay on Pygame. **View Last Match, Development Test replay and Evaluation replay** now prefer Spectator for supported two-entrant Active Sensing matches *when Spectator is installed or configured*. With Spectator absent or off, the route is the M2-5-qualified preflight followed by Pygame. These Spectator routes were qualified by the Spectator line, not by M2-5. |
| Gameplay, Ruleset, Agent API, replay/trace/result | No change. Engine changes are help text, the display-name table, the `spectator` dispatch and a command builder. Persisted identifiers and wire shapes are untouched, and the full-suite fixture and golden tests show zero outcome change (§7). |

## 5. Component-identity mappings

`battle_engine.ruleset_names` still maps exactly two identities:
`bytefray-rules-4` → **Classic** and `bytefray-rules-6-alpha1` → **Active
Sensing (Alpha)**. Historical and research IDs get no product name. Classic
remains the default on every surface. On the merged tree:

- `test_component_identity`: 37 passed.
- `test_release_compatibility_record`: 28 passed.
- `tools/release_compatibility.py --check`: exit 0, after the platform-text
  edits.
- `test_designer_ruleset_display_names` (GUI): passes.

The independent reviewer reached the same conclusion from source (§9).

## 6. Documentation updates (commit `cbca3b6`)

- **New `docs/v6/V6_ALPHA_M2_5_CLOSURE_01.md`.** It records the lead's
  acceptance of M2-5 PASS WITH CONDITIONS, the Ubuntu Wayland/XWayland
  confirmation and the native Xorg limitation, the carried conditions plus two
  new ones (C-X1 Xorg, C-X2 AC11), M2-6 deferred to 5.2, the identity-milestone
  acceptance, the continuing feature freeze and the reconciliation identities.
  It states that the Ubuntu evidence itself is not in the repository or on this
  workstation, and it restates no numbers from it.
- **`docs/ROADMAP.md`.** The status row now reads "M2-3, M2-4 and M2-5
  accepted; M2-6 deferred to 5.2". The 5.1 row says "Not authorized for
  release; feature freeze", records the identity acceptance, and records
  Spectator's proposed `0.1.0-alpha.1` subject to qualification. The M2
  narrative has the M2-5 disposition and conditions.
- **`README.md`.** The M2 status sentence that still said M2-5 was "awaiting
  authorization" is corrected.
- **Compatibility record JSON.** The Windows and Linux `bytefray` platform
  text no longer says "unmerged … awaits lead acceptance". The `.md` summary
  was regenerated with `--write`, and its hand-written M2-5 bullet updated.
  No identity, version or exposure value changed.

Left unchanged on purpose:

- All earlier M2-5 records (entry decision, public summary, Ubuntu handoff,
  manifest). They keep their historical wording, and the closure record
  supersedes their status.
- `docs/COMPONENT_IDENTITY_TRANSITION_REPORT.md`, which is a dated milestone
  report.
- `CHANGELOG.md` `[Unreleased]`, which lacks PD-1 and the M1/M2 features.
  Release notes belong to RC Preparation.
- The record's Spectator `version: null` and the policy's "first number is the
  lead's decision". `0.1.0-alpha.1` is only proposed until it is qualified;
  carrying it into the record belongs to RC Preparation.

## 7. Test results and baseline comparison

Environment: Windows 11 Pro 10.0.26120; Python 3.13.14 (`D:/Projects/BATTLE2/.venv`);
PySide6 6.11.2; pygame-ce 2.5.8. Linux: WSL2 Ubuntu 24.04.3 with the retained
M2-5 environment (Python 3.12.3, PySide6 6.12.0). Godot 4.7.2.

Each tree ran in its own detached worktree, with `PYTHONPATH` pinned to that
worktree (the venv's editable install points at the divergent main checkout)
and the default repo-local basetemp. The two parents ran **concurrently with the
merged tree**, under identical load.

### Full headless suite (`python -m pytest -rfE`)

| Tree | Passed | Failed | Errors | Skipped | Duration |
| --- | ---: | ---: | ---: | ---: | --- |
| M2-5 parent `bb6c4b8` | 8,684 | 86 | 3 | 33 | 1:34:56 |
| Identity parent `10da315` | 8,854 | 86 | 3 | 34 | 1:34:58 |
| **Merged `22f092c`** | **8,854** | **86** | **3** | **34** | 1:35:03 |

Per-node JUnit comparison:

- **Merged vs `10da315`:** 8,977 common nodes, **0 outcome changes**, 0 added,
  0 removed.
- **Merged vs `bb6c4b8`:** 8,806 common nodes, **0 outcome changes**. 171
  nodes are added from the identity line (170 passed; 1 skip, a POSIX-only
  permission test) and none is removed.
- **New failures: 0.** All three runs fail the **identical 89 node IDs**.

**Baseline failures, kept separate from regressions.** The 89 are present
unchanged on `bb6c4b8`, which differs from published `10c3530` only by a Qt
view, a `gui`-marked test and documents. They match the classes documented by
the Spectator and identity handoffs:

- 64 E9 v1/v2 freeze and integrity guards ("frozen engine manifest changed",
  "inherited immutable source/package boundary failed"). They pin every
  tracked `engine/src` file, and M1/M2 changed those files.
- 8 E8 analysis, family and runner freeze checks.
- 17 research-Ruleset "not product-selectable" assertions, which have been
  invalid since M1 exposed Active Sensing on `agents test`.
- The E9 `outside_repository` tmp_path case is included above. It is
  environmental under the mandated repo-local basetemp.

The full suites ran on `22f092c`. `cbca3b6` differs from it only in
documentation, so all 14 modules that read documentation were re-run on the
committed `cbca3b6` tree: **488 passed, 1 skipped**. They include the record
test, the install-docs consistency test, the E2–E8 matrix and fixture tests,
the M2-4 views test and `test_component_identity`.

### Designer and client GUI suite (established split)

| Part | Platform | `bb6c4b8` | `10da315` | **Merged** |
| --- | --- | ---: | ---: | ---: |
| `tests/` except History and M1-5 | offscreen | 399 | 412 | **412** |
| `test_v5_replay_history_browser.py` | offscreen | 96 | 96 | **96** (see note) |
| `test_v5_replay_history_qualification.py` | offscreen | 36 | 28 | **36** |
| `client/tests -m gui` | default | 13 | 13 | **13** |
| `test_v6_alpha_m1_5_designer.py` | native Windows | 8 | 8 | **8** |
| **Total** | | **552 / 552** | **557 / 557** | **565 / 565** |

At node level, the merged set is **exactly the union** of the parents' sets:
it contains the 8 M2-5-only cases and the 13 identity-only cases, and nothing
is missing or extra.

**Note: one unreproduced stall.** The first merged run of the History browser
module stalled after 25 tests, at
`test_entrant_search_is_debounced_into_one_query`. The process used 7 s of CPU
in 90 minutes. That run overlapped with three full suites and the Spectator
suite. It was stopped, and its log is retained. Four later runs of the same
module on the merged tree passed 96/96 (29–32 s each), with
`faulthandler_timeout=180` and no dump. Both parents also passed 96/96, one of
them under concurrent load (178 s). Neither line changes entrant search, the
debounce or the History worker. The stall is recorded as an intermittent,
load-associated test-harness stall in a pre-existing area, and it is not
attributed to the merge (§10).

### M2-5 focused gates on the merged tree

| Gate | Result |
| --- | --- |
| Windows, default zone (US Eastern): `-m gui -k 'date or calendar'` | **25 passed, 11 deselected**, matching the M2-5 publication validation |
| Linux WSL2, fresh process per zone; Qt zone and offset resolved first (UTC 0, Tokyo +32400, Indianapolis −14400) | **25 passed** in each zone |
| Linux attempt 1 (retained) | 16 setup errors and 9 passes in each zone: the fresh worktree lacked the `.pytest-tmp` parent. This is the same harness condition the M2-5 publication recorded. After adding `mkdir -p .pytest-tmp`, as the handoff specifies, it passed with no source change. |

Linux used offscreen Qt. That is regression evidence, not a native workflow
claim.

### Cross-repository (Spectator)

The full Spectator suite ran from a **fresh local clone** of `designer-integration`
`14089a7` with its push disabled, leaving the qualified clone untouched.
`BYTEFRAY_PRODUCTION_ROOT` pointed at the merged tree `cbca3b6`, `BYTEFRAY_ROOT`
at the pinned prototype `9c81718`, and `GODOT` at 4.7.2 console. Result:
**68 passed, 0 skipped, 0 failed** (10:41), the same as the Spectator handoff
baseline. The run included the production exporter reproducing the showcase and
production-sample documents byte for byte.

### Static checks on the merged tree

- `ruff check .` (0.16.3): all checks passed.
- `mypy engine/src/battle_engine`: no issues in 107 files.
- `mypy client/src/battle_client`: no issues in 20 files.
- `git diff --check`: clean.
- Relative links in the four changed or added Markdown files: 0 broken.

## 8. What was not run

- No native Ubuntu workflow on the merged tree: the Ubuntu confirmation
  applies to `bb6c4b8`.
- No Designer workflow with an installed Spectator.
- No human evaluation.
- No frozen PyInstaller build.
- No performance campaign.
- No M2-6 and no E9.

## 9. Independent adversarial review

Reviewer: Codex CLI 0.163.0 (OpenAI), a different model from the one that made
these changes. It ran in a read-only sandbox on a separate local clone with
pushing disabled, and no review refs reached the shared repository. It could
not run Python; its runtime claims are from source. It independently confirmed:

- the merge equalities and the absence of an evil merge;
- the 1,233/16/20 manifest accounting;
- protected-path preservation and the `5.0.0` version;
- the identity mappings;
- the Replay History route;
- the record's generated block, which it re-rendered itself;
- that the docs do not overclaim the Ubuntu confirmation.

Its verdict was **HOLD**, on these findings:

| # | Reviewer severity | Finding | Verification here | Disposition |
| --- | --- | --- | --- | --- |
| R1 | high | `client/src/battle_client/spectator_export.py:715` `_is_presentation_dir()` checks only filenames. `bytefray spectator export --replace` therefore accepts, and `_install()` then deletes with `rmtree`, a directory whose files merely have presentation names. | **Confirmed by reproduction.** A directory holding an unrelated `manifest.json` and `agent_a.json` passes `_check_output(..., replace_existing=True)`; a `notes.txt` directory is refused. This contradicts `docs/specs/spectator_export.md:82-83`: "only if it holds nothing but a presentation". It is reachable through the CLI with explicit `--replace`. Designer's `prepare --cache` path writes only into its own cache root. Inherited from `b3c4e8e`, not introduced by the merge. | **Open: release blocker** (§10). Rated medium-high here: irreversible deletion, but it needs explicit `--replace` and specific filenames. |
| R2 | medium | `app/widgets/spectator_launch.py:112`: a click for the same `result_path` as an in-flight job keeps the old job's pinned identities, so a completion for an earlier match at that path could open it. | **Plausible, not reachable through normal Designer use.** Every Designer match and Development Test gets a fresh unique run directory (`new_match_run_directory`; `agent_test` uses `exist_ok=False`). Triggering it needs an external rewrite of a run directory during an export. The result would be the earlier match, which had itself been preflighted and identity-verified. Inherited. | Open, low. Fix together with R1. |
| R3 | medium | The closure record pointed to this report before it existed. | Expected: this commit adds it. | Resolved by this commit. |

Fixing R1 and R2 was **not** done here. It would change the accepted, verified
Spectator implementation, which is outside this reconciliation's authority.

## 10. Unresolved qualification risks

1. **R1, data-loss defect in `bytefray spectator export --replace`** (confirmed,
   inherited). It must be fixed before any release candidate ships the
   command. Suggested scope: require positive presentation ownership, meaning a
   parseable Spectator manifest whose bindings match the documents, before
   moving a directory aside or deleting it. Add negative tests for unrelated
   files with the three reserved names. Re-run the Bytefray Spectator tests and
   the Spectator cross-repository suite.
2. **The Ubuntu Wayland/XWayland confirmation is not locally verifiable.** Its
   report and evidence are not in the repository or on this workstation. The
   closure record therefore rests on the lead's statement. Attach the report's
   location or SHA-256 to the closure record before RC qualification relies on
   it. Native Ubuntu on Xorg remains unqualified (C-X1).
3. **Spectator author metadata is not GitHub no-reply.** All 36 Spectator
   commits, including the 31 already published, are authored and committed as
   `personal-email identity (redacted)`. That includes the 5 unpublished `designer-integration`
   commits (`6f2eb38`, `34ef12b`, `810ac70`, `6756a66`, `14089a7`). Published
   commits cannot be changed without rewriting public history. The 5 local
   commits would have to be re-authored, with authorization, before any public
   Spectator publication if no-reply metadata is required. The Spectator
   clone's push URL is live. Bytefray commits here, including this
   integration, use the existing published identity `personal-email identity (redacted)`.
4. **The combined tree has no installed-Spectator Designer qualification.** The
   autouse `BYTEFRAY_SPECTATOR=off` fixture keeps every Designer GUI test on the
   Pygame route. Spectator's human, native-Linux and frozen-build checks remain
   open, as the compatibility record states.
5. **Intermittent History-browser stall** (§7). It did not reproduce in 4 runs
   on the merged tree, and both parents passed. Characterize it with a soak
   under load during RC qualification.
6. **The E9 and E8 freeze guards are red at baseline**, so they give no signal
   on further `engine/src` changes. E9 authority was verified directly: 329 pins,
   0 mismatches.
7. **Carried M2-5 conditions** (closure §4): replay load time, perspective-switch
   time, keyboard alternatives, WSLg focus, historical Linux crash observations,
   no display-scale or accessibility certification, and AC11 deferred with M2-6
   to 5.2.
8. **Release bookkeeping for RC Preparation:**
   - the version bump and its test pin;
   - moving the compatibility record to `candidate` and recording Spectator's
     proposed version;
   - CHANGELOG entries for PD-1 and M1/M2;
   - refreshing the untracked M2-6 participant instructions to the new UI
     labels before 5.2.

## 11. Recommendation

**HOLD** for Bytefray 5.1 Alpha Release Candidate Preparation.

The integration itself meets every reconciliation requirement:

- the merge is exact and conflict-free;
- the M2-5 qualified source, evidence, manifests and fixtures are preserved;
- E9 and Requirement C are unchanged;
- the identity mappings are intact;
- there are zero new failures across the headless, GUI, Linux timezone and
  cross-repository suites;
- the independent review is complete.

The HOLD rests on R1: a confirmed path to irreversible deletion of user files
in a command 5.1 would ship. Exit criteria:

1. A separately authorized, bounded fix for R1, and preferably R2, on this
   branch, re-reviewed independently. Re-run the Spectator export and launch
   tests and the Spectator cross-repository suite.
2. *(Recommended, not blocking RC Preparation start.)* The Ubuntu confirmation's
   location or SHA-256, attached to the M2-5 closure record.
3. *(Before any public Spectator publication.)* A decision on the author
   metadata (risk 3).

If the lead accepts R1 as a known limitation instead, every other condition for
READY is met.

## 12. Workspace state and evidence

Created in this session (all local; each can be removed once reviewed):

| Path | Purpose |
| --- | --- |
| `D:/Projects/BATTLE2-worktrees/m2-5-identity-integration` | branch `v6-m2-5-identity-integration` (this branch) |
| `D:/Projects/BATTLE2-worktrees/integration-merged-22f092c` | detached; merged full suite |
| `D:/Projects/BATTLE2-worktrees/integration-baseline-bb6c4b8` | detached; M2-5 parent baselines |
| `D:/Projects/BATTLE2-worktrees/integration-baseline-10da315` | detached; identity parent baselines |
| `D:/Projects/BATTLE2-worktrees/integration-linux-cbca3b6` | detached; Linux timezone, doc-consumer and Spectator production root |

Evidence lives in this worktree's git-ignored
`runs/integration_m2_5_identity_20261018/`, indexed by SHA-256 in
`artifact_index.json`. It holds:

- every JUnit and log;
- the merge-verification JSON;
- the before/after preservation snapshots;
- the Codex brief and review;
- the harness scripts.

Untouched:

- `D:/Projects/BATTLE2` (local `v6-research` `2fc3c82`);
- `work/v6-m2-clean`, including its uncommitted PD-1 copy and untracked M2-5
  records;
- the M2-5 publication checkout;
- `component-identity`;
- `spectator-integration`;
- all other worktrees;
- the Spectator clone.
