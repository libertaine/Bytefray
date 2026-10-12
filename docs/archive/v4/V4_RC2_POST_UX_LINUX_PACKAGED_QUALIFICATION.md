# Bytefray 4.0.0 RC2 — Post-UX Linux Packaged Qualification

Qualification date: 2026-09-08 (UTC).

## A. Candidate provenance

- Source branch: `origin/v4-rc2-development`.
- **Qualified candidate source SHA: `112a8a13640aeaa42febb3f4643493c8c31d92f1`.**
- `git fetch origin --prune` succeeded; `git rev-parse origin/v4-rc2-development` returned that exact SHA.
- Initial `pwd`: `/home/rod/Projects/BATTLE2`; initial branch: `v4-rc2-development`; initial HEAD: the candidate SHA.
- Remote fetch/push URL: `git@github.com:libertaine/Bytefray.git`.
- Initial `git status --short`: only `?? agents/Nemesis/agent.py-v1` and `?? dist_release_build/`. No tracked modifications. Both pre-existing items were preserved.
- Neither local nor remote `v4-rc2-linux-package-qualification` existed. Created that local branch directly at the candidate; no merge or reset.
- Source version: `4.0.0-rc2`; normalized Python distribution version: `4.0.0rc2`.
- **Qualification report commit:** the report-only commit containing this document, resolved with `git log -1 --format=%H -- docs/research/v4/V4_RC2_POST_UX_LINUX_PACKAGED_QUALIFICATION.md`. Its parent is the candidate above. The report commit is not the source revision qualified by this run.

## B. Linux environment

| Item | Observed value |
|---|---|
| Distribution | Ubuntu 26.04.1 LTS, Resolute Raccoon |
| Host | rod-HP-Pavilion-Notebook |
| Kernel | `7.0.0-30-generic #30-Ubuntu SMP PREEMPT_DYNAMIC Fri Jul 31 18:22:54 UTC 2026` |
| Architecture | x86_64 |
| Desktop | GNOME; `XDG_CURRENT_DESKTOP=ubuntu:GNOME` |
| Session | `XDG_SESSION_TYPE=wayland`, `WAYLAND_DISPLAY=wayland-0`, `DISPLAY=:0` |
| Shell-resolved `python3` | pyenv Python 3.11.9; pip 26.2 |
| Distro `/usr/bin/python3` | Python 3.14.4; pip 25.1.1 |
| Qualification Python | `/usr/bin/python3.14`, 3.14.4 |
| Build venv pip | 26.2.1 |
| Wheel/sdist/test venv pip | 25.1.1 |
| Git | 2.53.0 |
| GUI dependencies | pygame-ce 2.5.8, SDL 2.32.10, PySide6 6.11.2 |

The machine has a live Wayland session with XWayland available. Packaged graphical checks explicitly used native Wayland (`QT_QPA_PLATFORM=wayland`, `SDL_VIDEODRIVER=wayland`), confirmed by the running applications. Source automation used Qt offscreen and SDL dummy as identified below.

## C. Declared Python support

`pyproject.toml` declares `requires-python = ">=3.10"` with no upper bound; classifiers identify Python 3.10–3.14. The blocking Linux CI matrix tests 3.10, 3.11, 3.12, 3.13, and 3.14. The separate 3.15-dev job is explicitly experimental/non-blocking. Linux Pygame GUI CI covers 3.10 and 3.14; Designer GUI CI uses 3.10.

Installed supported interpreters found: pyenv 3.11.9 and distro 3.14.4. Official qualification here used 3.14.4 throughout. No forward-compatibility probe was applicable or performed; this report does not claim a local run of the entire CI interpreter matrix.

## D. Prior qualification precedent

Procedure references inspected:

- `V4_RC1_LINUX_PACKAGED_QUALIFICATION.md`, read from the historical local `v4-rc1-linux-package-qualification` branch: independent clean wheel/sdist installs, `/tmp` execution, import-origin guard, canonical matches/replay loading, native Wayland capture and event-driven smoke.
- `docs/research/v4/V4_RC2_PYGAME_CE_PYTHON314_QUALIFICATION.md`: supported Python 3.14/pygame-ce dependencies, sequential pytest discipline, GUI automation methods.
- `docs/research/v4/V4_RC2_LINUX_RELEASE_BASELINE_QUALIFICATION.md`: isolated runtime data, build and runtime evidence boundaries, Linux GUI/environment limitations. Its frozen-artifact procedure is distinct from this wheel/sdist run.
- Current `pyproject.toml`, `MANIFEST.in`, `tools/check_wheel.py`, `tools/build_linux.sh`, `.github/workflows/ci.yml`, `.github/workflows/linux-gui-smoke.yml`, README installation guidance, architecture and relevant test code.

Historical PASS results and Windows artifacts were not used as Linux qualification evidence. Their procedures and the explicitly known lint baseline were the only reused information.

## E. Artifact build

In commands below, `Q=/tmp/bytefray-rc2-post-ux-112a8a1`.

A new `Q/source` was populated exclusively by:

```bash
git archive 112a8a13640aeaa42febb3f4643493c8c31d92f1 | tar -x -C "$Q/source"
/usr/bin/python3.14 -m venv "$Q/build-venv"
"$Q/build-venv/bin/python" -m pip install --upgrade pip build
# cwd: Q/source
"$Q/build-venv/bin/python" -m build --outdir "$Q/artifacts"
```

Build completed successfully, producing an sdist and then a wheel from that sdist. Tools: Python 3.14.4, pip 26.2.1, build 1.6.0, packaging 26.3, pyproject_hooks 1.2.0; isolated backend dependencies setuptools 84.0.0 and wheel 0.48.0.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `bytefray-4.0.0rc2-py3-none-any.whl` | 922572 | `8232555d06ef9731441dde20bf772312f64cd5be12b2225a569b1c8c3c8c22eb` |
| `bytefray-4.0.0rc2.tar.gz` | 903382 | `435001a2476fc222e033b444605e0afa3739eb55f7bd37edd9b59fb0b6ca0fb6` |

Existing `dist_release_build/` wheel/sdist and root `bytefray.egg-info` were inspected and left untouched. Neither existing `dist/` nor `build/` supplied build input. The clean Git export excludes all untracked artifacts and old generated metadata. Qualification scripts, environments, logs, results, and screenshots live outside the exported source used to build the artifacts.

Metadata and contents: both artifacts report `bytefray`, `4.0.0rc2`, `>=3.10`. `tools/check_wheel.py` passed. The wheel contains 194 entries across `battle_engine`, `battle_client`, `app`, and distribution metadata, including packaged starters and branding. All four console scripts resolve to the expected functions:

```text
bytefray                = battle_engine.command:main
bytefray-cli            = battle_engine.cli:main
bytefray-agent-designer = app.agent_designer:main
bytefray-replay-viewer  = app.replay_viewer:main
```

The sdist contains 280 entries, including standard package metadata, source, README/license/build configuration and setuptools-included test sources. Archive inventories showed no qualification scratch files, venvs, bytecode/cache, old artifact trees, or `agent.py-v1`. The wheel validator also excluded pMARS distribution material. No twine dependency was introduced; the established wheel validator and direct archive metadata inspection were used.

## F. Wheel installation

Fresh environment: `Q/wheel-venv`, created with `/usr/bin/python3.14 -m venv`.

```bash
# cwd: /tmp
"$Q/wheel-venv/bin/python" -m pip install "$Q/artifacts/bytefray-4.0.0rc2-py3-none-any.whl"
"$Q/wheel-venv/bin/python" -m pip install "$Q/artifacts/bytefray-4.0.0rc2-py3-none-any.whl[replay,designer]"
"$Q/wheel-venv/bin/python" -m pip check
```

Core install succeeded with PyYAML 6.0.3. Declared GUI extras installed successfully afterward. `pip check`: exit 0, `No broken requirements found.`

Imports were asserted under `/tmp/bytefray-rc2-post-ux-112a8a1/wheel-venv/lib/python3.14/site-packages/`:

```text
battle_engine/__init__.py
battle_client/__init__.py
app/__init__.py
app/replay_viewer.py
app/agent_designer.py  (also verified in graphical smoke)
```

Every packaged smoke ran from `/tmp`, with `PYTHONPATH` removed and no editable install. `bytefray --version`, `bytefray --help`, `bytefray run --help`, and `bytefray-cli --help` exited 0. Version:

```text
Bytefray 4.0.0rc2, Agent API v2, result schema v1, replay schema v4, Python 3.14.4
```

## G. Sdist installation

Fresh independent environment: `Q/sdist-venv`, created with `/usr/bin/python3.14 -m venv`. No wheel was installed into it first.

```bash
# cwd: /tmp
"$Q/sdist-venv/bin/python" -m pip install "$Q/artifacts/bytefray-4.0.0rc2.tar.gz"
"$Q/sdist-venv/bin/python" -m pip check
```

Pip built and installed the sdist successfully with PyYAML 6.0.3. `pip check`: exit 0, `No broken requirements found.` Imports of `battle_engine`, `battle_client`, `app`, and `app.replay_viewer` were asserted beneath `/tmp/bytefray-rc2-post-ux-112a8a1/sdist-venv/lib/python3.14/site-packages/`, with the same relative module paths as §F. Version/help, two- and three-agent matches, replay parse/headless playback, defaults, POSIX picker logic, and compatibility smoke all passed independently from `/tmp`. No GUI extras were needed for the sdist's headless checks.

## H. Packaged two-agent match

Run independently with each environment's `bytefray` executable, using packaged starters copied into its isolated XDG data root:

```bash
bytefray run --a-type v4_quorum --b-type v4_defender_scout \
  --ruleset bytefray-rules-4 --seed 42 --ticks 3000 --arena 512 \
  --replay <Q/wheel-runs/two/replay.jsonl or Q/sdist-runs/two/replay.jsonl> --quiet
```

Both exits: 0. Both canonical results: `status=completed`, winner A, 11 ticks, `last_agent_standing`. A (`v4_quorum`) alive, score 16.0; B (`v4_defender_scout`) eliminated by `core_captured`, score 10.0. Result JSON, replay header, terminal replay result, and replay digest were parsed and cross-checked.

Both replay SHA-256 values: `3a1812c53d9206774eeed46864a18457563a018872eaaf95225afa3e2ed502fd`.

## I. Canonical scoring defaults

**PASS in both installations:**

```text
alive = 1.0
kill = 5.0
territory = 1.0
territory_bucket = 64
```

No scoring flags were passed. These values were asserted from actual `result.json` → `reproducibility.weights` and replay header → `config.weights`, for both two- and three-agent matches in both environments. The installed Designer's live Advanced controls independently displayed `1 / 5 / 1 / 64`. Source regression tests checked omission of untouched scoring flags and forwarding of explicit overrides.

## J. Packaged three-agent match

Same command as §H, adding only the supported `--c-type v4_claimer`, with separate `three/replay.jsonl` outputs. Both exits: 0. Ruleset: `bytefray-rules-4`; all entrants Agent API v2.

| Slot | Agent | Alive at termination | Score | Entrant termination |
|---|---|---|---:|---|
| A | v4_quorum | yes | 40.0 | none |
| B | v4_defender_scout | no | 4.0 | core_captured |
| C | v4_claimer | no | 29.0 | core_captured |

Both results: `completed`, winner A, 30 ticks, `last_agent_standing`. All three result entrants and replay-header entrants were asserted in A/B/C order. Installed replay rendering displayed all three HUD panels. The installed Designer also loaded this actual result through `read_match_presentation()` and `AdvancedPanel.show_result()`; its Results table was asserted and visually inspected with all three names, alive/eliminated statuses and scores (`designer-results-three.png`). No two-slot assumption was encountered in these exercised paths.

Both replay SHA-256 values: `3f7cc11acd99dc48607cc437d652f9a4e7a5c0a9a3c0da8f009b06a01d47d171`.

## K. Replay Viewer

- **Valid replay:** packaged `ReplaySession.load()` and standalone `bytefray-replay-viewer --replay <path> --renderer headless --tick-delay 0` passed for both matches in both environments; terminal winner matched result JSON.
- **Missing replay:** exit 2 with `Replay not found: <path>`; expected diagnostic rejection.
- **Malformed replay:** exit 1 with filename, line 1, and `invalid replay JSON`; no unhandled traceback.
- **No-argument standalone startup:** executed the wheel-installed console-script file using `runpy` with only the script name in `sys.argv`. The actual native Wayland display rendered 60 frames over approximately 4.06 seconds, then processed an injected Pygame QUIT and exited 0 with Pygame shut down. Captured `replay-empty.png` was visually inspected: **“No replay loaded” and “Open Replay...” present — PASS**. No argparse exit 2.
- **POSIX picker:** actual Linux execution of root enumeration, directory descent, parent navigation, selection, and canonical loading passed in both installs. `os.name == "posix"`, `ctypes.windll` absent, roots exactly `/`. Existing Linux picker tests also passed.
- **Graphical Open Replay:** a second no-argument launch processed real Pygame O/Enter events through the installed picker, selected the newly generated replay, and rendered playback. Captured `replay-pick.png` showed the three-entrant match at tick 19/30. Clean exit 0 after 120 frames.
- **Three-agent graphical replay:** installed viewer rendered A/B/C on native Wayland, then exited cleanly; capture `replay-three.png` inspected.

These are automated native-desktop checks with real Qt/SDL windows and application-surface captures. Instrumentation supplied capture timing and input/quit events; production parsing and rendering ran unchanged. They are separate from offscreen test results and are **not a human manual interactive attestation or compositor screenshot**.

## L. Agent Designer

The wheel-installed `bytefray-agent-designer` console script was executed through `runpy`; its real `main()` created and ran the application. A timed inspection after three seconds confirmed `QApplication.platformName() == "wayland"` and a visible window, then closed it cleanly (exit 0).

Automated widget interaction and visually inspected captures confirmed:

- Simple tab opens, with Ruleset, Arena Size, and the two-agent/Advanced guidance.
- Advanced opens; Ruleset row 0 precedes Agent A/B rows 2/3.
- Arena Size label; Kill Weight 5.000 and Territory Bucket Size 64.
- Add Agent exposes a populated, visible Agent C and Remove control.
- Remove returns to two entrants.

Captures: `designer-simple.png`, `designer-advanced.png`, `designer-agent-c.png`. Source offscreen tests separately cover Ruleset filtering, launch forwarding, scoring flag behavior, Results and replay lifecycle. The packaged real matches in §§H/J used the CLI; no claim is made that this run manually clicked through an entire installed Designer match workflow.

## M. Automated Linux tests

A fourth fresh environment, `Q/test-venv`, was installed with the declared `.[dev,replay,designer]` extras using an editable install of **only the clean candidate export**, for source tests. It was never used for installed-artifact smoke. Pytest 9.1.1; Python 3.14.4. All pytest suites ran sequentially, from `Q/source`, with the canonical repo-local `.pytest-tmp`/`.pytest-cache` configuration. No concurrent pytest runs shared those paths.

Test environment: `QT_QPA_PLATFORM=offscreen SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`. These GUI test results are offscreen/dummy results, separate from native Wayland package checks.

| Group | Passed | Failed | Skipped | Deselected | Elapsed |
|---|---:|---:|---:|---:|---:|
| Full canonical headless: `python -m pytest` | 2975 | 0 | 5 | 3 | 376.84 s |
| GUI: `python -m pytest -m gui tests/ client/tests/` | 306 | 0 | 0 | 484 | 40.19 s |
| Focused Phase 1–5: `python -m pytest -m '' <files below>` | 69 | 0 | 0 | 0 | 4.00 s |
| Ruleset compatibility | 268 | 0 | 0 | 0 | 25.32 s |
| Multi-agent | 244 | 0 | 0 | 0 | 17.27 s |
| Replay | 147 | 0 | 0 | 1 | 1.66 s |

Every invocation exited 0; groups overlap and counts must not be added as unique coverage.

Focused files:

```text
tests/test_advanced_panel_ux_labels.py
tests/test_phase2_advanced_ruleset_first.py
tests/test_phase4_advanced_multi_agent_roster.py
tests/test_phase5_scoring_defaults.py
tests/test_agent_designer_replay_lifecycle.py
tests/test_replay_browser_initial_directory.py
client/tests/test_replay_viewer_empty_state.py
client/tests/test_replay_picker.py
```

The following file sets were passed to `python -m pytest` under its normal `not gui` selection:

**Ruleset compatibility** (under `engine/tests/`):

```text
test_ruleset_agent_compatibility.py  test_ruleset_policy.py
test_ruleset_persistence.py  test_ruleset_v1_equivalence.py
test_ruleset_v2_runtime_compatibility.py
test_ruleset_v2_promotion_equivalence.py
test_v4_stable_ruleset_equivalence.py  test_v4_alpha2_placement.py
test_designer_ruleset_options.py
```

**Multi-agent:**

```text
engine/tests/test_v2_alpha4_multi_entrant.py
engine/tests/test_v4_spectator_multi_entrant.py
engine/tests/test_v2_default_placement.py
engine/tests/test_launchers.py
engine/tests/test_designer_workflows.py
client/tests/test_pygame_renderer.py
client/tests/test_replay_status.py
client/tests/test_headless_characterization.py
```

This includes v2/v4 multi-entrant engine behavior, real three-agent CLI placement/match cases, launch forwarding and multi-entrant renderer/status/HUD coverage.

**Replay:**

```text
engine/tests/test_replay_contract.py
engine/tests/test_replay_reconstruction.py
client/tests/test_replay_session.py
client/tests/test_replay_player_lifecycle.py
client/tests/test_replay_viewer_empty_state.py
client/tests/test_replay_picker.py
client/tests/test_playback_controller.py
```

The GUI empty-state test deselected in the replay-only invocation was explicitly included and passed in the focused and GUI groups.

## N. Static checks

Executed in the exact candidate export with the fresh test environment:

| Command | Result |
|---|---|
| `mypy engine/src/battle_engine` | exit 0; no issues in 102 source files |
| `mypy client/src/battle_client` | exit 0; no issues in 16 source files |
| `ruff check .` | exit 1; exactly two pre-existing RUF012 findings |

Ruff findings: mutable class attribute `_SIGNATURES` at line 63 of `agents/v4_quorum/agent.py` and `engine/src/battle_engine/data/starter_agents/v4_quorum/agent.py`. They match the known Windows qualification findings; `git diff b9e0766..112a8a1 -- <both files>` is empty. **Zero new findings.** No lint fixes, ignore changes, or application edits were made. Tools: mypy 2.3.1, Ruff 0.16.6.

## O. Cross-platform/path assessment

Installed CLI checks unset `BYTEFRAY_ROOT`, set isolated `XDG_DATA_HOME`, and asserted actual `get_data_root()` values of `Q/wheel-xdg/bytefray` and `Q/sdist-xdg/bytefray`. Matches populated those roots from packaged starter data. This exercised the installed Linux XDG branch, independent of repository paths.

POSIX picker execution passed with `/` roots and no Windows `ctypes.windll` available. Native Wayland launches and Linux replay/client tests found no accidental Windows-only dependency in the exercised paths.

## P. Artifact consistency

Wheel and sdist agree on version, API v2, result schema 1, replay schema 4, canonical defaults, all entrant records, winners, scores, tick counts, termination reasons and replay hashes for both match sizes. Independent compatibility matches also agree for omitted-Ruleset API-v2 resolution to stable v4, explicit v4 alpha1, explicit v4 alpha2, v2 with compatible Python agents, and v1 with VM starters.

The historical reports require identified artifact bytes and unchanged transport/runtime hashes, not identical hashes from independent rebuilds. No second-build reproducibility requirement was found, so no independent reproducibility build was performed or claimed. Artifact hashes were rechecked after qualification. No comparison was made against Windows artifacts from an earlier SHA.

## Q. Open findings

### Release blockers

None found. Every mandatory gate in this wheel/sdist qualification task passed. The known lint findings and explicitly bounded GUI evidence below are not new candidate defects.

### Non-blocking / V5 backlog

- The two acknowledged Quorum RUF012 findings remain unchanged.
- Setuptools warned about the existing license-table/classifier metadata deprecations. Build and artifact inspection passed; no metadata changes made.
- Native SDL Wayland startup reported unavailable libdecor GTK integration and fell back to undecorated windows. Rendering, picker operation and clean quit passed. This is recorded as an environment/presentation limitation, not a silent omission.
- Sandbox-only tool setup initially lacked network access; authorized dependency downloads succeeded outside that restriction. Sandbox launcher stream-fd/pip-cache warnings did not affect successful command outcomes.
- No human manual interactive attestation was collected in this run; real Wayland automated evidence and offscreen source tests are identified separately above.

## R. Repository state

Before writing this report, HEAD remained `112a8a13640aeaa42febb3f4643493c8c31d92f1`; `git status --short` still showed only the two original untracked items. All 733 candidate tracked files were compared between the clean repository checkout and the tested Git export after testing: zero differences. Tests/builds did not mutate tracked source. Artifact hashes remained unchanged.

Generated material:

- Durable local evidence copy: `dist/qualification-post-ux-linux-112a8a1/` (Git-ignored). Contains fresh `artifacts/` and `SHA256SUMS`, `logs/`, `screenshots/`, wheel/sdist match and compatibility result/replay directories, JSON evidence summaries, and qualification harnesses. None is staged.
- Original working area: `/tmp/bytefray-rc2-post-ux-112a8a1/`. Contains four fresh venvs (`build-venv`, `test-venv`, `wheel-venv`, `sdist-venv`), the clean source export and its build/egg-info/pytest/mypy/Ruff caches, isolated XDG/GUI roots, pip cache, and original evidence files. No existing development venv was reused.
- Pre-existing `agents/Nemesis/agent.py-v1`, `dist_release_build/`, and original egg-info were preserved.
- Branch: `v4-rc2-linux-package-qualification`, based directly on the candidate. The only committed change is this report. Its commit is local and report-only; no push, tag, merge, final version bump, publication, or release creation is part of this qualification.

Raw logs and artifact inventories are in the ignored evidence directory above; the report is the only tracked deliverable. The next activity, if authorized separately, is final release preparation, followed by rebuilding final artifacts and a fresh provenance/smoke gate.

## S. Qualification decision

LINUX PACKAGED QUALIFICATION PASSED — RC2 POST-UX LINUX GATE SATISFIED
