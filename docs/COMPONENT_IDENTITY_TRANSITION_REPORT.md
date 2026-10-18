# Component Identity and Versioning Reset — Transition Report

**Date:** 2026-10-18
**Branch:** `v6-component-identity` (local, unpushed)
**Outcome:** implemented and validated locally; ready for project-lead review.
Nothing was pushed, merged, tagged or published. No release branch exists,
and the runtime version is still `5.0.0`.

This milestone does **not** qualify Bytefray 5.1 Alpha or make it
releasable.

---

## A. Baseline

### Repositories and branches

| Repository | Path | Branch | Start | Final |
| --- | --- | --- | --- | --- |
| Bytefray (this work) | `D:/Projects/BATTLE2-worktrees/component-identity` | `v6-component-identity` | `1ac0d27705b76e470cabca689b500bcf242d2630` (tree `ecd1f69f…`) | code `c77771b86ea9d6204d8abb78d2f266b0763c4daa` (tree `df08be92…`); this report is added by the next commit, which changes nothing else |
| Bytefray-Spectator | `D:/Projects/Bytefray-Spectator-integration-20261017/spectator` | `designer-integration` | `14089a7bf624a5974346306a277e307ea8f48c07` (tree `9563b1b3…`) | unchanged |

### Choosing the starting commit

`1ac0d27` (`v6-spectator-integration`) was chosen as the starting commit. It
is the latest reviewed line that contains M1, M2-1 through M2-4 and the
Spectator integration. It is `10c3530` (= `origin/v6-research`, M2-4) plus
the five Spectator integration commits `b3c4e8e`, `9729fa6`, `33eb63c`,
`d0dc955` and `1ac0d27`. The worktree had untracked remediation logs only
and no tracked modifications.

### Unresolved lineage, recorded but not merged

- **M2-5 qualification line.** `v6-alpha1-m2-5-qualified` = `bb6c4b8` =
  `10c3530` plus one commit: the PD-1 Replay History date-filter fix
  (`app/views/replay_history.py`, 2 lines), its timezone test fixture and the
  M2-5 documents. Its worktree is
  `%TEMP%/bytefray-m2-5-publication-20261017-01/checkout`.
  `work/v6-m2-clean` holds the same two code changes uncommitted; its diff
  against `bb6c4b8` is empty. **This line is not in `1ac0d27` or in this
  branch.** A dry-run `git merge-tree` of this branch with `bb6c4b8` is
  conflict-free, and the two touch no common file. Reconciliation is the
  lead's decision, and the ROADMAP's M2-5 status row will need updating
  when it happens.
- **Divergent local `v6-research`.** The main checkout `D:/Projects/BATTLE2`
  is at `2fc3c82`: 4 ahead and 7 behind `origin/v6-research`, with a modified
  `README.md`. It was untouched. The venv's editable install points there,
  so every test run here set `PYTHONPATH` to the worktree under test.

### Preserved state (checked at start and end)

| Location | State |
| --- | --- |
| `D:/Projects/BATTLE2` | `2fc3c82` `v6-research`, `README.md` modified; untouched |
| `work/v6-m2-clean` | `10c3530`, PD-1 fix and fixture uncommitted; untouched |
| `BATTLE2-worktrees/spectator-integration` | `1ac0d27`, no tracked changes; untouched |
| Spectator `designer-integration` | `14089a7`, clean; untouched |
| other worktrees, branches and tags | untouched; no ref created except `v6-component-identity` and the detached baseline worktree below |

Added worktrees, all removable once the lead has reviewed:

- `component-identity`: this branch.
- `component-identity-baseline-1ac0d27`: detached, unmodified `1ac0d27`, used
  only for baseline test runs.
- `component-identity-final-2bf4f74`: detached, used only for the final full
  run.

The independent reviewer worked in a separate local clone in the session
scratchpad, with pushing disabled. The shared repository's `refs/codex/*`
count was 31 before and after the review, so no reviewer refs leaked into it.

---

## B. Final versioning policy

The authoritative policy is [docs/COMPONENT_VERSIONING.md](COMPONENT_VERSIONING.md).
In summary:

| Component | Convention |
| --- | --- |
| Bytefray application | SemVer 2.0.0 with dotted prereleases (`-alpha.N`, `-beta.N`, `-rc.N`). The tag is `v<semver>`, Python metadata uses the PEP 440 form (`5.1.0a1`), and the installer is named from the tag. MAJOR breaks a promise of the previous line; MINOR adds capability, including new Rulesets; PATCH changes no component identity. |
| Gameplay Rulesets | Immutable IDs: any gameplay-observable change gets a new ID. Lifecycle is a state in `ruleset_policy`, never a rename. Promotion registers a new stable ID, following the `-alpha11 → 2` and `-alpha2 → 4` precedent. The number is a Ruleset generation, unrelated to the application version. Future product IDs are `bytefray-rules-<G>[-<stage><N>]`, with 7 as the next unused generation. Future research IDs are `bytefray-rules-research-<code><nn>-<variant>`. |
| Ruleset display names | One table in `battle_engine.ruleset_names`, covering product-offered Rulesets only. Presentation only: never persisted, never input, never a compatibility key. Experimental names carry their stage. |
| Agent API | Integer generations only. Additions that leave existing agents unaffected use manifest capabilities (v1) plus Ruleset gating. |
| Replay, trace, result and other formats | (schema name, integer version). One written version, an explicit list of read versions, a bump on any change a strict reader would reject. No minor or prerelease format versions. |
| Bytefray Spectator | Its own SemVer series. No version exists yet, and the first number is the lead's decision. |
| Spectator presentation protocol | Integer manifest and document versions, bumped independently of both applications. |
| Research | Objective areas (MOB, CAP, VIS, MAD, SCH, INF), `<CODE>-<NN>` study IDs, no release numbers. Historical V3–V6/E2–E9 names are unchanged. |

**Historical identifiers that remain unchanged:** the 19 Ruleset ID
constants in `battle_engine.rules` and the six historical IDs in
`ruleset_policy`, Agent API 2, capabilities v1, `battle2.replay` 4 (reads
2–4), `battle2.result` 2 (reads 1–2), `bytefray.agent_trace` 2 (reads 1–2),
`bytefray.evaluation` 7/identity 7 (4–6 retired methodologies),
tournament/package/revision/preset/benchmark 1,
sensing demo/playback 1, the `bytefray.spectator_*` 1 schemas, Spectator
manifest 1 and 2 with documents 1, the Replay History cache, the fingerprint
and digest versions, every starter agent ID and manifest, and every recorded
`product_version`. The full inventory is in policy §5;
`engine/tests/test_component_identity.py` pins them.

**Future identifiers:** policy §4.2, §4.8 and §6. None was created.

---

## C. Naming changes

| Surface | Original label | New label | Canonical identity | File |
| --- | --- | --- | --- | --- |
| Designer Ruleset combo (Simple, Advanced, Development, Evaluation) | `Ruleset v4 — Current / Recommended` | `Classic — Recommended` | `bytefray-rules-4` | `app/services/ruleset_options.py` |
| Designer Ruleset combo (Advanced, Development) | `V6 alpha1 — Experimental sensing` | `Active Sensing (Alpha)` | `bytefray-rules-6-alpha1` | `app/services/ruleset_options.py` |
| Designer Ruleset item tooltip | none | `Ruleset ID: <id>` | both | `app/widgets/ruleset_combo.py` |
| Designer Ruleset tooltip/description | "Ruleset v4 is…; V6 alpha1 — Experimental sensing…; Window Scout requires this option" | "Classic (bytefray-rules-4) is…; Active Sensing (Alpha) (bytefray-rules-6-alpha1) is experimental…; Window Scout, Watchful Keeper and Roaming Reacquirer require it" | both | `app/services/ruleset_options.py` |
| Incompatible-agent explanation | `Select V6 alpha1 — Experimental sensing explicitly…` | `Select Active Sensing (Alpha) explicitly…` | `bytefray-rules-6-alpha1` | `app/widgets/ruleset_combo.py` |
| New Agent starting point | `Window Scout — V6 experimental sensing (personal copy)` | `Window Scout — personal copy` (matches the spec'd Keeper/Reacquirer labels) | n/a (template `window_scout`) | `app/views/development.py` |
| Development workflow hint | "select V6 alpha1 here/there" | "select Active Sensing (Alpha) here/there" | `bytefray-rules-6-alpha1` | `app/views/development.py` |
| Development guide button, tooltip, accessible name, dialog title | `V6 alpha1 sensing guide…` | `Active Sensing (Alpha) sensing guide…` | — | `app/views/development.py` |
| Replay History Ruleset column and filter | `Ruleset v4`, `Ruleset v6 alpha1` | `Classic`, `Active Sensing (Alpha)`; all other IDs unchanged (`Ruleset v4 alpha2`, …) | exact ID in tooltip and details | `app/services/replay_history_presentation.py` |
| Tournament results summary and match details | `Ruleset v4` (no ID anywhere) | summary `Classic` with tooltip `Ruleset ID: bytefray-rules-4`; details `Ruleset: Classic (bytefray-rules-4)` | `bytefray-rules-4` | `app/services/tournament_results.py`, `app/views/tournament.py` |
| Spectator fallback messages (6) | "classic replay viewer" | "Pygame replay viewer" | n/a; removes a collision with the Classic name | `app/widgets/spectator_launch.py` |
| Sensing guide header and footer (Designer and Pygame Help) | "V6 alpha1 experimental sensing: …"; "stable Ruleset v4 … V6 alpha1 …" | "Active Sensing (Alpha): …"; "Classic (bytefray-rules-4) … Active Sensing (Alpha) is bytefray-rules-6-alpha1 …" | both | `client/src/battle_client/sensing_presentation.py` |
| Sensing viewer window title | `Bytefray — Experimental sensing replay` | `Bytefray — Active Sensing (Alpha) replay` | — | `client/src/battle_client/renderers/sensing_renderer.py` |
| `bytefray run --ruleset` help | "… V6 alpha1 experimental sensing requires explicit selection" | "bytefray-rules-4 (Classic) is the default … bytefray-rules-6-alpha1 is Active Sensing (Alpha): experimental, it requires explicit selection" | both | `engine/src/battle_engine/cli.py` |
| `bytefray agents test --ruleset` help | IDs only | IDs plus display names | both | `engine/src/battle_engine/agent_test.py` |
| `bytefray --help` spectator line | "verify a V6 alpha1 match …" | "verify an Active Sensing (Alpha) match …" | — | `engine/src/battle_engine/command.py` |
| `bytefray spectator --help` | "Verify completed V6 alpha1 matches …" | "Verify completed two-entrant Active Sensing (Alpha) (bytefray-rules-6-alpha1) matches …" | — | `client/src/battle_client/spectator_export.py` (parser only) |

Deliberately unchanged:

- **Pygame replay HUD** (`Ruleset bytefray-rules-4 …`). This is technical
  replay output that already shows the canonical ID.
- **CLI stdout** (`ruleset: <id>`). It is diagnostic output, and Designer
  parses some CLI output.
- **Starter manifests** (`"display": "V6 Window Scout (Starter)"`) and
  starter IDs (`v6_*`). These are bound by starter content digests and
  scenario-card evidence.
- **`match_service` error text** "V6 alpha1 fixes scheduler chunk size 2…".
  It is a technical error on the research-only scheduler-override API.
  Changing it would edit a heavily evidence-bound module for no user benefit.
- **Spectator's own UI.** It shows the canonical `ruleset_id` in its title and
  footer. Showing a display name there would need a manifest change, which is
  out of scope, or a cosmetic Spectator change, which is not required.
- **Program and milestone names** in README and ROADMAP headings ("V6 Alpha
  1", M1/M2). These name the V6 program's stages, and the policy now says so
  explicitly.

---

## D. Compatibility declaration

The authoritative record is
[docs/releases/BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json](releases/BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json),
status **proposed**. Its generated summary and the qualification discussion
are in [BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.md](releases/BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.md).
`tools/release_compatibility.py --check` verified every code-checkable claim:

- Ruleset exposure on all 9 surfaces, found by parsing each CLI parser and
  reading each Designer option tuple;
- defaults and display names;
- the 14 research and 7 historical identities;
- Agent API and capabilities;
- replay, result, trace, evaluation, tournament and package versions;
- `bytefray --version` fields;
- the Spectator manifest and document schemas, provenance, entrants and
  perspectives.

Summary:

| | 5.1.0-alpha.1 (proposed) |
| --- | --- |
| Application | Bytefray `5.1.0-alpha.1` / `5.1.0a1` / tag `v5.1.0-alpha.1`; runtime still `5.0.0` |
| Default Ruleset | Classic (`bytefray-rules-4`), stable |
| Experimental | Active Sensing (Alpha) (`bytefray-rules-6-alpha1`), explicit only: CLI run/test/validate, Designer Advanced/Development |
| Agent API | v2 (v1 retired from execution) |
| Formats | replay 4 (reads 2–4), trace 2 (reads 1–2), result 2 (reads 1–2) |
| Spectator application | unreleased and unversioned; verified development source `designer-integration` `14089a7` |
| Spectator presentation | manifest: Bytefray writes 2, Spectator reads 1–2; documents v1; two-entrant Active Sensing only; Broadcast and Agent A |

**Qualified versus unqualified.** The code confirms these declarations, so
they are accurate. They are not release qualification.

- M1 is technically accepted (Windows AMD64, Linux X11/Xvfb).
- M2-2 through M2-4 are accepted with conditions.
- M2-5 reported PASS WITH CONDITIONS on the unmerged `bb6c4b8` line and
  awaits lead acceptance.
- Spectator has automated checks and a real Designer launch on Windows,
  headless checks on Linux, and no human or native-Linux-desktop
  qualification.
- 5.1.0-alpha.1 itself is unqualified.

**Known limitations** recorded in the record:

- Spectator handles two-entrant Active Sensing matches only, with Broadcast
  and Agent A perspectives.
- Pygame stays available. It opens instead of Spectator when Spectator is
  absent, does not support the match, or fails to export or launch.
- Pygame's A/B/Omni views are a separate capability from Spectator's
  perspectives.
- Three-agent Spectator is deferred, and human comprehension testing is
  deferred to 5.2.
- Classic is the default everywhere.
- Export time grows quadratically with match length.
- The frozen-build Spectator export is unverified.

**Unsupported combinations:**

- Active Sensing in Simple, in evaluation or in tournaments;
- execution of API v1, VM or Redcode agents (5.0.0 still runs them);
- new matches under historical IDs;
- Spectator for Classic, three-entrant, tournament or Replay History
  launches.

---

## E. Implementation

Commits on `v6-component-identity`, all local:

| Commit | Content |
| --- | --- |
| `283b3ed` | policy, display names, label changes, compatibility record and checker, documentation, tests |
| `2bf4f74` | fixes for Codex review 1: evaluation version 7/7 with a methodology-resolved check; capabilities-version check; a GUI assertion broken by the wording change; tournament canonical IDs; fallback wording; repair-versus-change policy distinction |
| `c77771b` | fixes for Codex review 2: retired research stays executable; `retired_from_execution` validated; evaluation check covers research Rulesets; "nonzero exit" wording |
| next commit | this report only |

**New files**

- `engine/src/battle_engine/ruleset_names.py`: the display-name table.
  Standard library only; it imports only `battle_engine.rules`.
- `docs/COMPONENT_VERSIONING.md`: the policy.
- `docs/releases/BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json` and its `.md`:
  the record and its generated summary.
- `tools/release_compatibility.py`: validates the record against the code
  and renders the summary.
- `engine/tests/test_component_identity.py`: pins every Ruleset ID, the
  wire-format identities and the Spectator contract. It checks the
  display-name rules (product-only, unique, never accepted by
  `--ruleset`/policy/alias) and Designer option IDs, order and default. It
  runs a real Classic and a real Active Sensing match and asserts that
  `result.json`, `replay.jsonl` and `trace.jsonl` carry the exact ID and no
  display name.
- `engine/tests/test_release_compatibility_record.py`: checks that the record
  agrees with the code and that the summary is current. Seventeen negative
  controls prove the checker catches disagreements.
- `tests/test_designer_ruleset_display_names.py` (gui): checks the visible
  labels, item tooltips and defaults on Simple, Advanced, Development, New
  Agent and Evaluation. It also checks that a sensing agent in Development
  does not switch the Ruleset.

**Modified source (presentation only).**

- `app/services/ruleset_options.py`, `app/widgets/ruleset_combo.py`,
  `app/views/development.py`, `app/services/replay_history_presentation.py`,
  `app/widgets/spectator_launch.py`, `app/services/tournament_results.py`,
  `app/views/tournament.py`.
- `client/src/battle_client/sensing_presentation.py`,
  `client/src/battle_client/renderers/sensing_renderer.py`.
- `client/src/battle_client/spectator_export.py`: the argparse description
  only.
- `engine/src/battle_engine/cli.py`, `engine/src/battle_engine/agent_test.py`
  and `engine/src/battle_engine/command.py`: help text only.

No change touches selection, filtering, capability checks, serialization,
gameplay, the exporter's projection or verification, or any persisted
identifier.

**Modified tests (expected-label updates only, nothing weakened).**

- `engine/tests/test_v5_replay_history_presentation.py`: `bytefray-rules-4`
  now expects `Classic`. Cases were added for `bytefray-rules-6-alpha1`,
  `bytefray-rules-4-alpha2` and a research ID, proving historical and
  research labels are unchanged.
- `tests/test_v5_alpha1_phase4_tournament_results.py`: `Ruleset v4` →
  `Classic`, plus new assertions for the ID tooltip and the
  `Classic (bytefray-rules-4)` details line.
- `tests/test_agent_designer_spectator.py`: the failed-export warning text
  `classic replay viewer` → `Pygame replay viewer`. The warning, the
  fresh-preflight and the fallback assertions are unchanged.

**Documentation.**

- README: identity table with display names, policy and record links,
  product wording in the CLI/Designer/Spectator lines.
- ROADMAP: status table says "V6 program", gives display names and links
  the record.
- COMPATIBILITY: policy link and new axis rows (display name, Spectator
  protocol, Spectator application). A "Current development line" section
  states that the 2B.9–2B.12 retirements apply here, while the existing 5.0.0
  section remains as the 5.0.0 description. The legacy matrix now includes
  `bytefray-rules-6-alpha1`.
- AGENT_AUTHORING: tells users to select **Active Sensing (Alpha)**. The
  Designer never displayed the ID the old text named.
- INSTALL and `docs/specs/spectator_export.md`: product wording.
- AGENTS.md: a compatibility rule and a lookup-table row for the policy.

**CHANGELOG.** `[Unreleased]` gains "Changed — component names and
versioning policy" and the missing "Removed — Agent API v1, VM/blob
execution and Rulesets 1 and 2" (V6 Phase 2B.12) entry. Three Unreleased
sentences that 2B.12 had made false were corrected:

- "`bytefray-rules-1`/`-2` remain executable", which appeared twice;
- "the Ruleset-2 equivalence test survives". The module was deleted in
  `3caf143`; it is still present in `v5.0.0`.

Every released section, from `[5.0.0]` down, is byte-identical (same
SHA-256 before and after).

**Spectator repository:** no change. No cross-repository requirement exists.
The presentation contract is unchanged, and Spectator already shows canonical
IDs.

**Deliberately deferred to the RC-preparation milestone:**

- the version bump and its test (`test_v5_alpha1_phase_b_engine_hygiene`
  pins `5.0.0` across `pyproject.toml`, `installer.iss` and metadata);
- 5.1 release notes for M1/M2 features, which CHANGELOG `[Unreleased]` does
  not yet describe;
- moving the record from `proposed` to `candidate`;
- refreshing the M2-6 participant instructions (untracked, other lineage) to
  the new UI labels, if M2-6 ever runs.

---

## F. Validation

Environment: Windows 11 Pro 10.0.26120, Python 3.13.14 (`D:/Projects/BATTLE2/.venv`),
Godot 4.7.2. Every run set `PYTHONPATH` to the worktree under test, because the
venv's editable install points at the divergent main checkout. Every run used
the default repo-local `--basetemp` from `pytest.ini`, and each full run ran in
its own worktree.

### Full headless suite: baseline compared with final

Command, in each worktree:
`python -m pytest -rfE --junitxml=<file>`

| Run | Commit | Passed | Failed | Errors | Skipped |
| --- | --- | ---: | ---: | ---: | ---: |
| Baseline | `1ac0d27` (unmodified) | 8,789 | 86 | 3 | 34 |
| Final | `2bf4f74` | 8,852 | 86 | 3 | 34 |

Per-test comparison of the two JUnit files:

- **New failures: 0. Tests that changed outcome: 0.**
- Both runs fail the identical 89 node IDs.
- The 63 extra passes are the new tests: 37 in `test_component_identity`
  and 26 in `test_release_compatibility_record`.

The 89 shared failures are the pre-existing classes the Spectator
integration handoff already documented:

- E9 v2/instrument freeze guards, which pin every tracked `engine/src` file
  and were broken by M1/M2 at `10c3530`;
- E8 freeze checks;
- research-ruleset "not selectable from product surfaces" assertions,
  invalidated since M1 put Active Sensing on `agents test`.

88 of them match the handoff's `10c3530` list exactly. The 89th,
`test_v6_e9_v2_independent_consumers.py::test_production_source_checker_rehashes_real_files_and_adoption[outside_repository]`,
also fails on unmodified `1ac0d27`. It assumes `tmp_path` lies outside the
repository, but the mandated repo-local basetemp puts it inside, so the fault
is never detected. It is environmental and pre-existing, not an
identity-migration defect. No test was weakened or skipped to get a result.

The checker-only commit `c77771b`, which changes no runtime code:

- `engine/tests/test_release_compatibility_record.py`: **28 passed, 0
  failed**;
- `tools/release_compatibility.py … --check`: exit 0.

### Designer GUI suite: baseline compared with final

The four-way split is the handoff's. The combined offscreen run hits the known
pre-existing Replay History crash, and the M1-5 tests need the native Qt
platform.

Command: `python -m pytest -m gui <part>`.

| Part | Platform | Baseline `1ac0d27` | Final (`2bf4f74` code) |
| --- | --- | ---: | ---: |
| `tests/` except history and M1-5 | offscreen | 409 passed | 412 passed |
| `test_v5_replay_history_browser.py` | offscreen | 96 passed | 96 passed |
| `test_v5_replay_history_qualification.py` | offscreen | 28 passed | 28 passed |
| `test_v6_alpha_m1_5_designer.py` | native | 8 passed | 8 passed |
| **Total** | | **541, 0 failed** | **544, 0 failed** |

Per-test comparison: no new failures, nothing removed. The 3 additions are
`tests/test_designer_ruleset_display_names.py`.

### Targeted proofs required by the mission

| Requirement | Evidence |
| --- | --- |
| Selections resolve to the same canonical IDs | `test_designer_options_keep_identity_order_and_default`, `test_cli_ruleset_choices_and_default_are_canonical_identities`, GUI `test_simple_and_advanced_show_display_names_and_default_to_classic` |
| Default stays Classic (`bytefray-rules-4`) | the same tests, plus checker `default ruleset` checks on CLI and Designer |
| Explicit Active Sensing selection in Advanced and Development | GUI display-name tests and existing `test_v6_alpha_m1_5_designer` (8 passed, native) |
| Capability validation unchanged | existing `test_designer_ruleset_compatibility`, `test_ruleset_agent_compatibility` and `test_v6_alpha_m1_policy_capabilities` pass, with no outcome change; a sensing agent in Development does not switch the Ruleset (new GUI test) |
| Agent API v2 contracts unchanged | `test_wire_format_identities_are_unchanged`; the full suite's API v2 tests show no outcome change |
| Existing replay, result and trace files readable and verifiable | full-suite fixture tests show no outcome change. A read-only pass over all 38 real results in `D:/Projects/BATTLE2/runs/_designer` covered 5 Rulesets (2, 4, 4-alpha1, 4-alpha2, 6-alpha1) and result schemas 1 and 2. All passed `preflight_result_replay`, all 17 Active Sensing runs passed `reconstruct_sensing_playback`, and the directory's SHA-256 manifest was identical before and after |
| Historical identities neither rewritten nor aliased | `test_historical_identities_are_recognised_but_never_executable_or_aliased`, `test_only_the_documented_historical_alias_exists`, `test_research_and_unknown_identities_have_no_display_name`; Replay History labels for historical IDs unchanged |
| Display names never persisted or accepted | `test_match_artifacts_record_the_exact_identity_and_no_display_name` runs real Classic and Active Sensing matches; `test_a_display_name_is_never_accepted_as_a_ruleset_identity`; `bytefray run --ruleset Classic` gives `invalid choice` |
| Spectator export accepts the same matches; unsupported ones fall back | `client/tests/test_spectator_export.py` and `engine/tests/test_spectator_viewer_service.py` pass; GUI `test_agent_designer_spectator.py` passes (fallback paths); Spectator `exporter/tests/test_production_presentations.py` with `BYTEFRAY_PRODUCTION_ROOT` at the final worktree: **8 passed**, showcase and production-sample documents byte-identical, tampered copy rejected |
| Manifest versions and integrity checks unchanged | `test_spectator_presentation_contract_is_unchanged`; the Spectator acceptance above; the exporter's projection and verification code is untouched (only its argparse description changed) |
| No protected research artifact modified | `git diff 1ac0d27 c77771b` touches none of `docs/v6`, `docs/research`, `docs/archive`, `tools/research`, `engine/src/battle_engine/data`, `_legacy`, `agents`, `assets`, fixtures, screenshots, `rules.py`, `ruleset_policy.py`, `match_service.py`, `sensing_playback.py`, `sensing.py`, `replay.py`, `result_model.py`, `agent_trace.py`, `agent_api.py`, `pyproject.toml` or `installer.iss`; no binary file changed |
| Released CHANGELOG entries accurate | everything from `## [5.0.0]` down is byte-identical (SHA-256 `bb6e5d09…`); corrected Unreleased claims checked against Git history and the `v5.0.0` tag |

### Static checks

- `ruff check .`: all checks passed.
- `mypy engine/src/battle_engine`: no issues, 107 files.
- `mypy client/src/battle_client`: no issues, 20 files.
- Documentation: every relative link in the 11 changed or added Markdown
  files resolves. `tools/release_compatibility.py --check` exits 0, so the
  JSON, the generated summary and the code agree.

### Independent adversarial review

Reviewer: Codex CLI 0.163.0 (OpenAI), a model that did not write the change.
It worked in a read-only sandbox on a separate clone.

| Pass | Scope | Result | Disposition |
| --- | --- | --- | --- |
| 1 | `1ac0d27..283b3ed`, full brief | no high; 4 medium, 1 low, 1 policy question | all fixed in `2bf4f74` (see §E) |
| 2 | `283b3ed..2bf4f74` plus the cumulative diff | 5 of 6 resolved; 1 low residual; 2 new medium (retired-research wording, unchecked `retired_from_execution`) | all fixed in `c77771b` |
| 3 | `2bf4f74..c77771b` | **all resolved; no medium or high defects remain.** It traced all 15 evaluate choices to schema and identity 7 | closed |

Across all three passes the reviewer found:

- no persisted-ID change and no display-name leak;
- no runtime change disguised as relabelling;
- no change to the Spectator schema contract;
- no scope expansion.

The reviewer could not execute Python inside its sandbox, so every claim it
made rests on reading the source. The test runs above were the implementer's.

---

## G. Release readiness

**Ready to adopt.** The policy, display names, compatibility record and
documentation are complete. The full regression and GUI comparisons show no
new failures, and the independent review is closed. Persisted contracts and
protected evidence are byte-for-byte unchanged.

**Decisions for the project lead:**

1. Accept the milestone and choose how to integrate `v6-component-identity`.
   It sits on top of the Spectator integration line (`1ac0d27`).
2. Reconcile the M2-5 line (`bb6c4b8`). It merges with this branch without
   conflict. Update ROADMAP's M2-5 status row at the same time.
3. Confirm policy §4.1's transition note. Strict SemVer would class ending
   Agent API v1 execution as MAJOR; the policy records "5.1" as a one-time
   decision taken before the policy existed.
4. Confirm the display names "Classic" and "Active Sensing (Alpha)". A
   residual overlap remains with Spectator's own "Classic" memory style;
   renaming that is optional and belongs to Spectator.
5. Choose Spectator's first version number and its publication timing.
6. Accept or adjust the future Ruleset and research ID conventions (policy
   §4.2 and §4.8).

**Safe to begin 5.1 Alpha Release Candidate Preparation:** yes, once the lead
accepts this milestone and decides items 1–2. That milestone still owns:

- the runtime version bump to `5.1.0a1`, with tag `v5.1.0-alpha.1`,
  `installer.iss` and the `test_v5_alpha1_phase_b_engine_hygiene` update;
- moving the record from `proposed` to `candidate`;
- 5.1 release notes for the M1/M2 features;
- a frozen-build check of `bytefray spectator`;
- release qualification itself.

**Bytefray 5.1 Alpha is not qualified or releasable** on the strength of this
milestone. Nothing was pushed, merged, tagged, branched for release or
published.

---

## Appendix — Version-coupling audit

Classification:

1. persisted contract identity;
2. runtime compatibility dependency;
3. user-facing label;
4. documentation terminology;
5. historical reference;
6. future naming convention.

**Application version**

| File | Coupling | Class | Disposition |
| --- | --- | --- | --- |
| `pyproject.toml` `version = "5.0.0"` | application version; becomes `product_version` | 1, 2 | unchanged; bump belongs to RC prep |
| `tools/installer.iss` `AppVersion`/`ReleaseTag` | application version; installer file name `Bytefray-Setup-{ReleaseTag}` | 2 | unchanged; matches policy §4.1 |
| `engine/src/battle_engine/project_info.py` / `bytefray --version` | prints app, Agent API, result and replay versions on one line | 3 | unchanged; the checker validates its fields against the record |
| `engine/src/battle_engine/result_model.py` `product_version` | persisted producing-application identity | 1 | unchanged; policy §3 defines its meaning |
| `client/src/battle_client/spectator_export.py` `exporter_identity`, manifest `bytefray.version` | app version plus source digest for cache validity; Spectator requires only non-empty | 1, 2 | unchanged; a future version bump cannot break Spectator |
| `engine/tests/test_v5_alpha1_phase_b_engine_hygiene.py` | pins `5.0.0` across pyproject, installer and metadata | 2 | unchanged; RC prep updates it with the bump |
| `engine/tests/test_check_wheel.py`, `test_result_model.py`, `test_replay_history.py` | `5.0.0a1`/`rc1` fixture strings | 5 | unchanged |

**Rulesets**

| File | Coupling | Class | Disposition |
| --- | --- | --- | --- |
| `engine/src/battle_engine/rules.py` (19 ID constants), `ruleset_policy.py` (historical IDs, lifecycle sets, registry, `OMITTED_RULESET_CANDIDATES`) | Ruleset identities and exposure | 1, 2 | unchanged; pinned by the new tests |
| ID numbers `-4`, `-6-alpha1`, `-6-research-*` | number once tracked an app major or the V6 program | 5, 6 | not renumbered; policy §4.2 recasts it as a generation number with an explicit future convention |
| `rules._RULESET_ALIASES` (`evaluation-rules-1`) | historical alias | 1 | unchanged; pinned |

**Agent API**

| File | Coupling | Class | Disposition |
| --- | --- | --- | --- |
| `agent_api.AGENT_API_VERSION` 2, `SUPPORTED_AGENT_API_VERSIONS` {2} | Agent API | 1, 2 | unchanged; pinned |
| `agent_capabilities` v1 (`sense`) | manifest capability contract | 1 | unchanged; checker validates it |
| `agent_scaffold` `--api-version` and `--template` help | names the canonical IDs | 3 | unchanged (already accurate) |

**CLI**

| File | Coupling | Class | Disposition |
| --- | --- | --- | --- |
| `cli.py`, `agent_test.py`, `agent_validation.py`, `evaluation_cli.py`, `tournament_cli.py` `--ruleset` choices | canonical IDs as input | 2 | unchanged; display names rejected (tested) |
| `cli.py` `--ruleset` help "V6 alpha1 experimental sensing" | research/program label used as a product name | 3 | changed |
| `agent_test.py` `--ruleset` help | IDs only | 3 | display names added |
| `command.py` spectator help; `spectator_export.py` parser description | "V6 alpha1 match" | 3 | changed |
| `cli.py` "Window Scout requires explicit --ruleset bytefray-rules-6-alpha1 (experimental sensing)" | names the canonical ID | 3 | unchanged |
| CLI stdout `ruleset: <id>` lines | diagnostic output, partly parsed by Designer | 2 | unchanged |
| `match_service.py` "V6 alpha1 fixes scheduler chunk size 2…" | research-API error text | 3 | deferred: evidence-bound module, technical audience |

**Designer**

| File | Coupling | Class | Disposition |
| --- | --- | --- | --- |
| `app/services/ruleset_options.py` labels, `RULESET_DESCRIPTION` | "Ruleset v4 — Current / Recommended", "V6 alpha1 — Experimental sensing"; description said only Window Scout needs alpha1 | 3, 4 | changed to the central display names; description corrected |
| `app/widgets/ruleset_combo.py` | explanation text; no ID visible | 3 | changed; item tooltip shows the ID |
| Simple, Advanced, Development, Evaluation tabs | all populate from `ruleset_options` | 3 | changed through the central table; selection is by `itemData` (ID) only |
| `app/views/development.py` template label "Window Scout — V6 experimental sensing (personal copy)", workflow hint, guide button/title | program label as a product name | 3 | changed |
| Starter manifests (`"display": "V6 Window Scout (Starter)"`), starter IDs `v4_*`/`v5_*`/`v6_*` | digest-bound agent identities | 1 | unchanged; policy §4.9 names future starters by behavior |
| `app/views/evaluation.py` and `app/services/designer_workflows.py` "retired in V6 Phase 2B.12" | names the phase that retired a feature | 5 | unchanged |
| `app/widgets/spectator_launch.py` "classic replay viewer" | collides with the Classic name | 3 | changed to "Pygame replay viewer" |
| `app/agent_designer.py` `_open_classic_result_replay`; test name `…keep_the_classic_viewer` | internal identifiers | — | unchanged (not user-facing) |

**Replay, result and history surfaces**

| File | Coupling | Class | Disposition |
| --- | --- | --- | --- |
| `app/services/replay_history_presentation.py` `_readable_ruleset` | shape-derived "Ruleset v6 alpha1" | 3 | product IDs use display names; every other ID unchanged; ID kept in tooltip and details |
| `app/services/tournament_results.py`, `app/views/tournament.py` | summary and details via `ruleset_label` | 3 | display name, with the ID in details and tooltip (review fix) |
| `client/src/battle_client/replay_status.py` / Pygame HUD | bare canonical ID | 3 | unchanged on purpose (technical) |
| Replay History SQLite cache (schema 2) | stores `ruleset_id` | 1 | unchanged |
| `engine/src/battle_engine/replay_integrity.py` preflight | ID-agnostic verification | 2 | unchanged |

**Sensing and Spectator**

| File | Coupling | Class | Disposition |
| --- | --- | --- | --- |
| `sensing_playback.EXPECTED_RULESET_ID`, `battle_client.sensing` | runtime gate on the alpha1 ID | 2 | unchanged |
| `sensing_presentation` guide header/footer; `sensing_renderer` caption | "V6 alpha1 experimental sensing" | 3 | changed |
| `sensing_presentation.ALPHA1_TEACHING_PROFILE`, `SCENARIO_CARDS` starter digests | technical profile; digest-bound evidence | 1, 3 | unchanged |
| `spectator_export` manifest/document schemas and versions, provenance, entrants, ruleset gate, `EXPORTER_VERSION` | presentation contract | 1, 2 | unchanged; pinned and checked |
| Spectator `fixture_loader.gd` (`MANIFEST_VERSIONS [1, 2]`), `broadcast_effects.gd` (`SENSE_HALF_WIDTH` keyed by ID), title/footer show the ID | reader contract | 1, 2 | unchanged; no Spectator change |
| Spectator application version | none exists | 6 | policy §4.6: own series; first number is the lead's decision |
| Spectator "Classic" memory style | overlaps the Classic name | 3 | left as is (different app, different context); noted for the Spectator lead |
| Spectator `bytefray.pin.json` | legacy exporter source pin | 1 | unchanged |

**Documentation**

| File | Coupling | Class | Disposition |
| --- | --- | --- | --- |
| `README.md` identity table, CLI/Designer/Spectator lines | IDs without names; "V6 alpha1 match" | 4 | updated |
| `docs/ROADMAP.md` status table "Version / Identity: V6" | program shown as if a version | 4 | updated; M2-5 status row left for the M2-5 lineage |
| `docs/COMPATIBILITY.md` "Current V5 product boundary" | still described 5.0.0 behavior as current | 4 | new current-line section; the 5.0.0 section kept and labeled |
| `docs/COMPATIBILITY.md` axis table, legacy matrix | no display-name, Spectator or alpha1 entries | 4 | rows added |
| `CHANGELOG.md` `[Unreleased]` | three statements false after 2B.12; 2B.12 entry missing | 4 | corrected and added; released entries byte-identical |
| `docs/AGENT_AUTHORING.md` | told users to select an ID the UI never displayed | 4 | updated |
| `INSTALL.md`, `docs/specs/spectator_export.md` | "V6 alpha1 matches" | 4 | updated |
| `docs/specs/agent_scaffold.md` | spec'd starter labels, canonical IDs | 4 | unchanged (accurate; Window Scout label now follows its pattern) |
| `ARCHITECTURE.md` ("current V6 architecture", "V6 Phase N"), `docs/FUTURE_PLANS.md` | program and phase names | 4, 5 | unchanged; policy §3 defines "V6" as a program name |
| `docs/v6/**`, `docs/research/**`, `docs/archive/**`, `tools/research/**`, evidence JSON | historical records | 5 | unchanged (verified: zero diff) |

**Research**

| File | Coupling | Class | Disposition |
| --- | --- | --- | --- |
| V3–V6 programs, E2–E9 study IDs, freeze IDs | program and version-style names | 5 | unchanged; E9 LOCKED and Requirement C NOT ESTABLISHED untouched |
| Future studies | — | 6 | policy §4.8 objective areas; no study created |
