# Bytefray 5.1 Pre-RC Remediation 02 — Python Wheel Completeness and Active Sensing Agent Distribution

**Task ID:** P1 Remediation 02 (release blocker identified by Gemini Argon's 5.1 Alpha release-readiness review)

**Affected component:** setuptools wheel/sdist packaging (`pyproject.toml`) and the release wheel gate (`tools/check_wheel.py`)

**Remediation worktree:** `D:\Projects\BATTLE2-worktrees\p1-remediation-02-wheel`

**Remediation branch:** `v6-p1-remediation-02-wheel` (local, unpushed)

**Base commit:** `a1aff900e2b2de613af82b04ed6b7c46295e99fc` (`a1aff90`, accepted P1 Remediation 01)

**Result:** **PASS WITH CONDITIONS — no remaining blocking packaging defects.** Every registered starter agent and every scaffold template was verified in a non-editable wheel installation on Windows and on Ubuntu (WSL2). The conditions are scope boundaries, not open defects; see §G.4 and §G.5.

**Independent review:** Codex CLI 0.163.0 (read-only, isolated clone). Round 1: **CHANGES REQUIRED** (one P2, one P3). Correction `f9b9da9`. Round 2: **APPROVE WITH NOTES** (P3 documentation note, addressed in §G.4).

Evidence is retained under the worktree's ignored `work/p1-remediation-02-20261019-01/` (`SHA256SUMS.txt` lists the artifacts and scripts).

---

## A. Baseline

| Item | Observation |
|---|---|
| Starting SHA | `a1aff900e2b2de613af82b04ed6b7c46295e99fc`, present locally |
| Relationship to `0863846` | Direct child: `0863846` is an ancestor (`git merge-base --is-ancestor`) and `0863846..a1aff90` is exactly one commit, the P1-01 Spectator `--replace` remediation (3 files) |
| Originating P1-01 worktree | `D:\Projects\BATTLE2-worktrees\p1-remediation-01-spectator-replace` at `a1aff90`, clean (ignored files only) before and after this milestone |
| New worktree / branch | Created with `git worktree add -b v6-p1-remediation-02-wheel … a1aff900e2b2de613af82b04ed6b7c46295e99fc`; clean at creation |
| Version metadata | `pyproject.toml` `version = "5.0.0"`; installed `bytefray --version` → `Bytefray 5.0.0, Agent API v2, result schema v2, replay schema v4`. Unchanged. |
| Build environment (Windows) | Windows 11 Pro 10.0.26120; `python -m build` 1.6.0 from the repository `.venv` (CPython 3.13); isolated build environments resolved `setuptools 84.2.0` (wheel `Generator` field) |
| Clean-install interpreters | python.org CPython 3.13.7 and 3.10.8 (Windows); CPython 3.12.3 on Ubuntu 24.04.3 LTS under WSL2 (kernel 6.6.87.2-microsoft-standard-WSL2) |

**Packaging configuration as found.** `include-package-data = false`; `[tool.setuptools.packages.find]` scans `engine/src`, `client/src` and `.` for `battle_engine*`, `battle_client*`, `app*`, with setuptools' default namespace-package discovery; `battle_engine` package-data listed the two v2 templates and `data/starter_agents/v4_*/*`, `data/starter_agents/v5_*/*`; `exclude-package-data` strips bytecode; `MANIFEST.in` prunes retired data directories, which affects only the sdist. The frozen PyInstaller specs collect the entire `starter_agents/` tree through `tools/packaging_data.collect_data_tree`, independently of `pyproject.toml`. CI's `build-linux-wheel` job runs `python -m build --wheel` and then `tools/check_wheel.py`.

## B. Root cause

### B.1 What the baseline artifacts actually contained

Argon's static finding was confirmed by building `a1aff90` from a pristine `git archive` export through both setuptools paths and inspecting the archives:

| Artifact (built from `a1aff90`) | Entries | V6 `agent.yaml` (×3) | V6 `agent.py` (×3) | Retired research modules (×3) | Teaching-fixture `agent.py` (×3) | Old `check_wheel.py` |
|---|---:|---|---|---|---|---|
| `python -m build --wheel` (CI path) | 182 | **missing** | shipped | **shipped** | shipped | **fails** (retired resources) |
| `python -m build` (sdist → wheel) | 179 | **missing** | shipped | pruned | shipped | **passes** |
| sdist | 185 | **missing** | shipped | pruned | shipped | — |

The omission was partial. Setuptools' namespace-package discovery treated every `battle_engine/data/**` directory containing a `.py` file as a package, so the V6 `agent.py` modules shipped as code while their `agent.yaml` manifests — reachable only through package-data — did not. The same discovery shipped `data/reference_agents/core_seeker/agent.py`, `data/v3_closeout_agents/turtle_core_refresher/agent.py` and `data/v3_phase7_agents/core_tracker_offset/agent.py` on the CI path. The existing gate therefore failed CI's own wheel for an unrelated reason, while it passed the sdist-path wheel because its hand-maintained `EXPECTED_FILES` never listed the V6 starters.

### B.2 Installed behaviour (reproduced)

The sdist-path baseline wheel was installed into a fresh venv outside the repository with a disposable data root (`baseline-runtime-repro.log`):

- `bytefray agents` printed `starter bootstrap completed with errors` (`Starter agent 'v6_…' is missing manifest`) for all three, listed only the 10 V4/V5 starters, and **exited 0**.
- `bytefray agents create … --template window_scout|watchful_keeper|roaming_reacquirer` each failed with exit 2 (`No such file or directory: …\v6_*\agent.yaml`); `--template blank` worked.
- `agents validate v6_window_scout --ruleset bytefray-rules-6-alpha1` and an Alpha1 `bytefray run` both failed: `Unknown agent 'v6_window_scout'`.

### B.3 Why source and editable testing did not detect it

In a source checkout and in an editable install, `battle_engine.paths.get_resource_root()` resolves to the repository, so bootstrap, discovery, scaffolding and every existing test read `engine/src/battle_engine/data` directly. The frozen executables bundle the whole `starter_agents/` directory, so they were unaffected too. Only the setuptools path consults the package-data globs, and the one wheel gate checked a hardcoded list rather than the runtime registry. The gap was already recorded as limitation L3 in [M2-3 Closure 01](../v6/V6_ALPHA_M2_3_CLOSURE_01.md) and carried in [M2-4 Closure 01](../v6/V6_ALPHA_M2_4_CLOSURE_01.md) ("the v6 sensing starters remain absent from the wheel `package-data` globs; packaging is outside M2 qualification"). This remediation closes it.

### B.4 Original versus corrected wheel

| Build path | Removed by the correction | Added by the correction |
|---|---|---|
| CI path (182 → 179 entries) | `data/reference_agents/core_seeker/agent.py`, `data/v3_closeout_agents/turtle_core_refresher/agent.py`, `data/v3_phase7_agents/core_tracker_offset/agent.py`, `data/teaching_fixtures/{v6_encroaching_opponent,v6_relocating_opponent,v6_stationary_opponent}/agent.py` | `data/starter_agents/{v6_window_scout,v6_watchful_keeper,v6_roaming_reacquirer}/agent.yaml` |
| sdist path (179 → 179) | the three teaching-fixture `agent.py` files | the three V6 `agent.yaml` |
| sdist (185 → 185) | the three teaching-fixture `agent.py` files | the three V6 `agent.yaml` |

No code module and no other resource changed. The corrected CI-path and sdist-path wheels have identical entry sets (`artifact-inventory.json`), and the Linux-built wheel's entry set is identical to the Windows-built one (`linux/wsl_qualify.log`).

## C. Resource inventory

Source of truth: `battle_engine.starters.STARTER_AGENT_NAMES`, which bootstrap installs, and `battle_engine.agent_scaffold.TEMPLATE_DIRECTORIES_BY_API_VERSION`, which `agents create --template` offers. Every registered starter is distribution-supported, because bootstrap installs all of them into the writable catalog. All starters are Agent API v2 Python agents whose manifest entrypoint is `agent.py:create_agent`, and every shipped directory's content digest equals the runtime pin `CURRENT_STARTER_DIGESTS`.

| Starter | Bundled files | Personal-copy template | Ruleset requirement |
|---|---|---|---|
| `v4_claimer`, `v4_concentrated_attacker`, `v4_defender_scout`, `v4_local_defender`, `v4_scout` | `agent.yaml`, `agent.py` | — | Classic default |
| `v4_quorum` | `agent.yaml`, `agent.py`, `README.md` | — | Classic default |
| `v5_region_attacker`, `v5_scout_striker`, `v5_core_defender`, `v5_dual_team` | `agent.yaml`, `agent.py` | — | Classic default |
| `v6_window_scout` (Window Scout) | `agent.yaml`, `agent.py` | `window_scout` | `capabilities.required = [sense]` → explicit `bytefray-rules-6-alpha1` |
| `v6_watchful_keeper` (Watchful Keeper) | `agent.yaml`, `agent.py` | `watchful_keeper` | same |
| `v6_roaming_reacquirer` (Roaming Reacquirer) | `agent.yaml`, `agent.py` | `roaming_reacquirer` | same |

| Template (Agent API v2) | Resource directory | Files (`TEMPLATE_FILES`) |
|---|---|---|
| `blank` (default) | `data/agent_template_v2` | `agent.yaml`, `agent.py` |
| `annotated` | `data/agent_template_v2_annotated` | same |
| `window_scout`, `watchful_keeper`, `roaming_reacquirer` | `data/starter_agents/v6_*` | same |

**Deliberately not distributed:** `data/teaching_fixtures/*`, the M2 opponents used only by the source-tree teaching demonstrations (§G.4), plus `data/reference_agents`, `data/v3_closeout_agents`, `data/v3_phase7_agents` and `data/benchmarks`, all retired by V6 Phase 2B.12. All of them remain tracked in the repository.

## D. Implementation

Commits `ff30490` (implementation) and `f9b9da9` (review correction). `a1aff90..f9b9da9`: 4 files, +825 / −52.

| File | Change |
|---|---|
| `pyproject.toml` | Adds `data/starter_agents/v6_*/*` to `battle_engine` package-data; adds `exclude = ["battle_engine.data", "battle_engine.data.*"]` to `packages.find`; comments name the registries the patterns must cover. |
| `tools/check_wheel.py` | Registry-derived starter/template validation (below). Its forbidden-file, pMARS, bytecode, entry-point and metadata checks are unchanged. |
| `engine/tests/test_check_wheel.py` | Rewritten: registry-generated contract tests on synthetic wheels carrying the real package modules and bundled bytes. |
| `engine/tests/test_wheel_packaging.py` | New: package-data model test and real built-wheel artifact tests. |

**Package-data pattern.** `data/starter_agents/v6_*/*` is correct for setuptools: package-data globs are relative to the package directory, select files only, and `*` does not descend. The existing `exclude-package-data` rules strip any bytecode. The V4/V5 patterns are preserved and the rule is no broader than its siblings. A built wheel confirms it selects exactly `agent.yaml` and `agent.py` for each V6 starter.

**Discovery exclusion.** Excluding `battle_engine.data*` from package discovery is the minimal change that makes resources ship through package-data alone. Without it, the CI-path wheel keeps shipping the three retired modules that the existing gate forbids, and any future omission stays partial and silent. No product code imports `battle_engine.data…`; it is imported only by research tooling and tests in the source tree. Installed starters and copies are loaded by file path from the writable catalog, as the installed probes in §E confirm.

**Wheel checker.** `validate_wheel` now:

1. extracts the wheel and imports `battle_engine.starters` and `battle_engine.agent_scaffold` from it in a separate `sys.executable -I -B` interpreter, refusing either module if it resolves outside the extraction. The checker therefore sees the registry exactly as the installed runtime builds it. That import chain is standard-library only, so this runs in CI's bare build job.
2. for every registered starter, requires `agent.yaml` (JSON, `name` equal to the directory), the entrypoint's implementation file, and a shipped-content digest, computed with the wheel's own `starter_content_digest`, equal to the pinned `CURRENT_STARTER_DIGESTS` entry. This catches any missing, extra or altered file, `README.md` included.
3. for every template in `TEMPLATE_DIRECTORIES_BY_API_VERSION`, requires every `TEMPLATE_FILES` entry.
4. rejects any `battle_engine/data/` entry outside a registered starter or template directory, which covers teaching fixtures, research data and stray directories.
5. fails closed if the registries cannot load or are empty.

The hardcoded V4/V5/template entries were removed from `EXPECTED_FILES`; the package markers and the branding icon remain. `validate_wheel` now returns a `WheelSummary`, and the CLI prints the validated starters and templates.

**Regression tests added** (mapped to the required cases):

| Required case | Protection |
|---|---|
| 1, 4, 5, 6 — every registered starter ships `agent.yaml` and `agent.py`, V4/V5 retained, V6 present | `test_validator_rejects_any_missing_registered_resource` (one case per registered file, generated from the registries); `test_built_wheel_ships_every_registered_resource_exactly` (real wheel: each starter directory's file set and bytes equal the source); `test_checker_fails_the_real_wheel_without_one_starter_manifest[<each starter>]` |
| 2 — every template packaged | generated omission cases; `test_a_newly_registered_template_is_required_without_editing_the_checker` |
| 7 — package-data covers the registry | `test_package_data_patterns_select_every_registered_resource` evaluates the globs the way setuptools does, without a build |
| 8 — checker fails on one omission | the omission cases above; newly registered starter/template; conditional, augmented and call-time registration; modified content; manifest identity; unregistered resources; unloadable registries |
| 9 — installed resolution without a checkout | `test_installed_wheel_layout_resolves_every_resource_without_a_checkout`: the real wheel unpacked and exercised under `-I -S` with only the stdlib and a private PyYAML copy. It bootstraps every starter, scaffolds every template, discovers and loads all agents, checks digests and capability contracts, and fails if any module resolves from the checkout. |

Expectations are derived from the runtime registries, so a newly registered starter or template is covered without editing a list. The artifact tests build a real wheel offline from the tracked and unignored build inputs, or take a prebuilt one through `BYTEFRAY_WHEEL`, mirroring `BYTEFRAY_FROZEN_EXE`. Run against the unfixed `a1aff90` packaging and wheels, the final tests fail **8** times (sdist-path wheel) and **18** times (CI-path wheel) (`before-new-tests-final-*-summary.log`). At `f9b9da9` they give **81 passed**.

## E. Clean-install qualification

### E.1 Artifacts

| Artifact | SHA-256 | Entries |
|---|---|---:|
| Final `f9b9da9` CI-path wheel (Windows), `bytefray-5.0.0-py3-none-any.whl` | `162c5e76b98f28f23805b6d06b5079fe460e68257b7cc69ceb58ddacc6fc41bd` | 179 |
| Final `f9b9da9` Linux-built wheel | `3501d9323be1edea2fa8ea376eb3286dba765beb019ebff859f8d8b8ede6863e` | 179 |
| `ff30490` CI-path wheel (Windows) | `f9c1154e55635d6a75994483156be5ad60327c6bf1af45861549f0588a9fcd47` | 179 |
| `ff30490` sdist-path wheel (Windows) | `4f48eeec5f9ed58705a3ba64ee282a228a2dbb53436c46b34bb58e4a2643fd06` | 179 |
| `ff30490` sdist | `852f8d91e1eb7b36f5dbea443ed228d7ba9e6cfcaa8253454cd05e236ee6ac97` | 185 |
| `ff30490` Linux-built wheel | `b884e60e40d9910976adba6328cb4070eddccf14a20a35cf582b187961d88769` | 179 |
| Baseline `a1aff90` CI-path / sdist-path wheel | `3b1c782f…010aa` / `703c0bf8…9c112d` | 182 / 179 |

`f9b9da9` changes only the checker and tests, none of which enter the wheel. Its wheel is entry-for-entry content-identical to the `ff30490` wheel; only zip timestamps differ (`final-vs-ff30490-wheel-content.txt`).

### E.2 Commands

```text
git archive <commit> | tar -x -C <export>                                  # pristine source, no checkout debris
python -m build --wheel --outdir <dist> <export>                           # CI path (isolated build)
python -m build --outdir <dist> <export>                                   # sdist → wheel path
python tools/check_wheel.py <dist>/bytefray-5.0.0-py3-none-any.whl
<base python> -I qualify_installed_wheel.py --wheel <whl> --work <dir outside every checkout> \
    --forbid D:\Projects\BATTLE2 --forbid D:\Projects\BATTLE2-worktrees   # §E.3
```

### E.3 Isolation

The qualification driver (`scripts/qualify_installed_wheel.py`, SHA-256 `735a77f2…`) runs from a base interpreter in isolated mode, outside every checkout. It then:

- creates a fresh venv and installs the wheel with `pip install <wheel>`, non-editable; PyYAML 6.0.3 is the only dependency.
- drives the installed `bytefray` console script with a curated environment: all `PYTHON*` and `BYTEFRAY_*` variables, `VIRTUAL_ENV`, `PWD`/`OLDPWD` and any `PATH` entry under a checkout removed; `PYTHONNOUSERSITE=1`; `BYTEFRAY_ROOT` set to a disposable data root; working directory also disposable.
- fails if any environment value names a checkout.

An installed-import probe recorded, for the final Windows run:

```text
battle_engine  …\qual-win-py313-f9b9da9\venv\Lib\site-packages\battle_engine\__init__.py
resource root  …\qual-win-py313-f9b9da9\venv\Lib\site-packages
data root      …\qual-win-py313-f9b9da9\data          (the disposable BYTEFRAY_ROOT)
checkout root  None                                    (paths._source_checkout_root)
direct_url     archive_info sha256=162c5e76…           (no editable dir_info)
v6_window_scout / v6_watchful_keeper / v6_roaming_reacquirer
               …\site-packages\battle_engine\data\starter_agents\v6_*  [agent.py, agent.yaml]
```

The same probe found no `sys.path` entry and no loaded module under either checkout root, and no editable-install marker in site-packages. Linux recorded the equivalent `…/p1r02-qual-f9b9da9/qual/venv/lib/python3.12/site-packages` paths.

### E.4 Acceptance cases

All results below are from the final-commit Windows run (101/101 checks). The Linux run of the final commit's Linux-built wheel produced the same results (101/101).

| # | Case | Result |
|---|---|---|
| 1 | Wheel inventory | All 13 registered starters, including the three V6, under site-packages with their pinned digests; all 5 templates complete. Corrected checker passes every candidate wheel. |
| 2 | Starter bootstrap | `bytefray agents` exit 0, no bootstrap errors; all 13 starters copied into the fresh data root; second run silent and byte-identical. |
| 3 | Discovery | All 13 listed, including `V6 Window Scout (Starter)`, `V6 Watchful Keeper (Starter)`, `V6 Roaming Reacquirer (Starter)`. |
| 4 | Personal copies | `agents create p1r02_<t> --template <t>` exit 0 for `window_scout`, `watchful_keeper`, `roaming_reacquirer`, `blank` and `annotated`. The V6 copies' manifests name the copy, keep `api_version: 2` and keep `capabilities.required: [sense]`. |
| 5 | Validation | Each V6 copy and each bundled V6 starter: `status: valid`, `api_version: 2` under `--ruleset bytefray-rules-6-alpha1` (dry-run actions `SENSE operand=91` for Window Scout and Roaming Reacquirer, `READ operand=0` for Watchful Keeper). Without `--ruleset`, each copy is refused, exit 2, `code: agent_capability_unsupported`, `Ruleset 'bytefray-rules-4' does not provide required capabilities: sense`. |
| 6 | Bounded Alpha1 execution | For each V6 copy against its bundled starter: `bytefray run --ruleset bytefray-rules-6-alpha1 --ticks 60 --seed 11`, run twice. Both runs exit 0, `ruleset_id` is `bytefray-rules-6-alpha1`, and each entrant's recorded `source_sha256` equals the installed wheel's `agent.py`. `replay.jsonl` and `summary.json` are byte-identical between the two runs. `agents test <copy> --ruleset bytefray-rules-6-alpha1 --ticks 60` exits 0 (`ticks: 60/60`, `termination: tick_limit`). The replays are also byte-identical between Windows and Linux (`5e1eb999…`, `d33e4120…`, `0739efc6…`). |
| 7 | Classic compatibility | All 10 V4/V5 starters and the `blank`/`annotated` copies are `status: valid` with no `--ruleset`. A `v4_scout` vs `v5_core_defender` run without `--ruleset` records `bytefray-rules-4`. A sensing copy without `--ruleset` is refused (exit 2), so Active Sensing still needs explicit selection. |
| 8 | Source independence | §E.3. All runtime output stayed under the disposable work directory. |
| 9 | Platform coverage | Table below. |

| Platform | Interpreter | Wheel | Checks |
|---|---|---|---|
| Windows 11 Pro 10.0.26120 | CPython 3.13.7 | final `f9b9da9` CI-path (`162c5e76…`) | **101/101** |
| Windows 11 Pro 10.0.26120 | CPython 3.13.7 | `ff30490` CI-path (`f9c1154e…`) | **101/101** |
| Windows 11 Pro 10.0.26120 | CPython 3.10.8 | `ff30490` sdist-path (`4f48eeec…`) | **101/101** |
| Ubuntu 24.04.3 LTS (WSL2) | CPython 3.12.3 | final `f9b9da9` Linux-built (`3501d932…`) | **101/101** |
| Ubuntu 24.04.3 LTS (WSL2) | CPython 3.12.3 | `ff30490` Linux-built (`b884e60e…`) and Windows-built (`f9c1154e…`) | **101/101** each |
| Windows / Ubuntu (WSL2) | 3.13.7 / 3.12.3 | **control:** baseline `a1aff90` sdist-path | **47/65** each: all 18 failures are V6 (missing installed resources, bootstrap errors, discovery, three `agents create` failures, data-root copies) |

On Ubuntu the corrected checker passed the Linux-built wheel, and the corrected regression modules gave 81 passed against it via `BYTEFRAY_WHEEL`.

The Linux evidence is from Ubuntu under WSL2 on the same host. It is a real Linux kernel and filesystem, but it is not bare-metal or another distribution; see §G.5.

## F. Regression and review

### F.1 Tests (Windows; `PYTHONPATH` bound to the worktree)

| Run | Tree | Result |
|---|---|---|
| New/updated modules (`test_check_wheel.py`, `test_wheel_packaging.py`) | `f9b9da9` | **81 passed** (`focused-new-04.log`) |
| Same modules against unfixed `a1aff90` packaging/wheels | `a1aff90` + new tests | **8 failed** (sdist path), **18 failed** (CI path), as intended |
| Focused regression: wheel/packaging, frozen-resource, starter bootstrap/refresh, scaffold, paths, version hygiene, command/CLI, validation/test, V6 Window Scout / Keeper / Reacquirer, component identity, compatibility record, Spectator viewer service and the P1-01 exporter suite | `ff30490` | **890 passed, 11 skipped** (`regression-01.log`). The skips are 8 opt-in frozen-executable smokes and the 3 Windows platform skips also recorded by P1-01. |
| Full headless suite (`python -m pytest`, pytest.ini defaults, run concurrently in two detached helper worktrees) | `ff30490` | **8,994 passed, 86 failed, 3 errors, 36 skipped** (1:38:54) |
| Same | `a1aff90` | 8,928 passed, 86 failed, 3 errors, 36 skipped (1:38:51) |

Per-node JUnit comparison (`full/compare_full.txt`):

- **`ff30490` vs `a1aff90`:** 9,048 common nodes, **0 outcome changes, 0 new failures**. The 71 added nodes all pass; they are the new and rewritten wheel tests. The 5 removed nodes are the replaced `test_check_wheel` cases, which passed before.
- **`ff30490` vs merged `22f092c`**, the reconciliation's documented baseline: **0 outcome changes, 0 new failures**. The 89 failing nodes are **identical** to the documented inherited 89 (E9/E8 freeze and integrity guards, research-Ruleset selectability assertions, and the E9 `outside_repository` case under the repo-local basetemp). None was suppressed.
- `f9b9da9` changes only `tools/check_wheel.py` and the two wheel test modules; no other test imports the checker. Those modules were rerun at `f9b9da9` (81 passed). The 14 documentation-consuming modules identified by the reconciliation gave **488 passed, 1 skipped** with this report present, the same result as at `cbca3b6`.

### F.2 Static checks

- `ruff check .`: all checks passed.
- `mypy engine/src/battle_engine`: 107 source files clean. `mypy client/src/battle_client`: 20 source files clean. `mypy tools/check_wheel.py` and `mypy --explicit-package-bases` on both new test modules: clean.
- `tools/release_compatibility.py --check docs/releases/BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json`: passed.
- `git diff --check`: clean.

### F.3 Independent review

Codex CLI 0.163.0 ran in a separate local clone with the push URL disabled, under `exec -s read-only`. The brief was fed from a file, so stdin reached EOF and the earlier stdin hang could not recur, and each round had a hard `timeout`. Round 1 took 3 min 42 s and round 2 took 2 min 34 s. The shared repository's 24 pre-existing `refs/codex/*` refs were unchanged. Briefs and reports are under `review/`.

| Round | Verdict | Findings | Disposition |
|---|---|---|---|
| 1 (`ff30490`) | CHANGES REQUIRED | **P2:** the checker's AST registry reader ignored registrations inside module-level `if`/`try`/loop blocks or made by calls at import, so a stale registry could pass an incomplete wheel. **P3:** `sensing_playback.verify_keeper_scenario()`/`verify_reacquirer_scenario()` also need the teaching fixtures. | P2 corrected in `f9b9da9`: the registries are imported from the extracted wheel, and the digest uses the wheel's own function. Tests were added for conditional, augmented and call-time registration, a computed roster and unloadable registries. P3 is documented in §G.4. |
| 2 (`f9b9da9`) | APPROVE WITH NOTES | P2 resolved; no new P1/P2. The P3 note carries forward. The reviewer notes the checker relies on a trusted build environment, because system-site `.pth` hooks still run under `-I`. | Accepted; §G.5. |

Round 1 also listed `regression-01.log` and `sensing-demo-installed-probe.log` as absent. Both were in the review bundle, and round 2 confirmed it. On the real wheels, the baseline digests computed by the round-2 checker equal those its round-1 reimplementation had computed, independent confirmation that the replaced code was faithful.

The task allowed Gemini Argon or Codex. Codex was used, because it is available here as a non-interactive CLI with a read-only sandbox.

## G. Scope and compatibility

### G.1 Evidence and protected state

| Protected item | Verification |
|---|---|
| P1-01 worktree | `a1aff90`, clean. P1-01 exporter tests pass in the focused regression set. |
| M2-5 reconciliation worktree | `0863846`, clean |
| Main `v6-research` checkout | HEAD unchanged at `2fc3c82`; its working tree was not modified |
| `work/v6-m2-clean` | `10c3530`, the same 19 pre-existing status lines |
| Spectator repository | `14089a7` (`designer-integration`), clean; not used or modified |
| M2-5 qualified source identity ([source manifest](../v6/V6_ALPHA_M2_5_SOURCE_MANIFEST_01.json), 1,249 pins) | Unmodified. Against it, only `tools/check_wheel.py` and `engine/tests/test_check_wheel.py` newly differ at this branch, both authorized here. The 21 differences already present at `a1aff90` are unchanged (`m2-5-source-manifest-delta.txt`). |
| E9 | No `engine/src` file changed; E9 remains **LOCKED** |
| Replay/trace/result artifacts, historical evidence, frozen showcase/sample documents, Spectator schemas | Not touched |

Every qualification venv, data root and output directory was created outside the repositories; pytest used its mandated repo-local `.pytest-tmp`. Existing `dist/`, `build/`, `runs/` and evidence directories were not used or modified.

### G.2 Runtime contracts unchanged

No file under `engine/src`, `client/src` or `app` changed. Agent implementations, starter identities and contents (digests equal their pins in every wheel), ruleset IDs, Agent API v2, manifests and capability metadata, match semantics, teaching demonstrations, and ruleset defaults are unchanged. Classic remains the default and Active Sensing (Alpha) remains explicit (§E.4 cases 5 and 7). The application version remains `5.0.0`, and the component versioning policy is untouched.

### G.3 Requirement and roadmap status

Requirement C remains **NOT ESTABLISHED**. M2-6 human comprehension work remains deferred to 5.2. No 5.1 RC preparation, P2 Spectator launcher work, release branch or tag was started.

### G.4 `battle_engine.sensing_demo` distribution boundary

| Question | Finding |
|---|---|
| Documented as a supported installed-user command? | **No.** It has no console script and no `bytefray` subcommand, and README/INSTALL do not mention it. Every documented invocation is `.venv\Scripts\python.exe -m battle_engine.sensing_demo` in a source checkout, in the M1/M2 qualification records. |
| Development/research demonstration tool? | **Yes.** It produces the M1/M2 teaching-demonstration evidence (`demo.json` sidecar) from source-tree opponents (`data/teaching_fixtures`, described as "Not a public starter" in M2 Checkpoint B). The M1 contract lists "complete wheel assets/clean installs" as later alpha-wide work. |
| Does packaging contradict the distribution contract? | **No contradiction with a supported surface.** From any wheel, before and after this change, it fails cleanly with exit 2 and writes nothing. Baseline: `does not support entrant metadata … Agent API None`, because the manifests were missing. Corrected: `Teaching agent directory 'v6_stationary_opponent' not found`. Keeper and Reacquirer also require output under `get_resource_root()/runs/v6_alpha_m2`, which for an installed wheel is site-packages, and they reject a writable data root (`sensing-demo-installed-probe.log`). The installed replay client uses `sensing_playback.verify_demonstration_artifacts`/`reconstruct_sensing_playback`, which need no fixtures. |
| Safe to classify as source-only for 5.1? | **Yes.** The source-only boundary covers `battle_engine.sensing_demo` and, per review finding P3, `sensing_playback.verify_keeper_scenario()` / `verify_reacquirer_scenario()`, which also resolve the teaching fixtures. Supporting them from a wheel would require shipping the fixtures and changing the protected M2-5 output-root logic. That is outside this authorization, and no supported installed surface depends on it, so no escalation is required for 5.1. |

The corrected packaging stops shipping the fixtures' partial `agent.py` files (§B.4). This removes nothing functional: no wheel ever shipped their manifests.

### G.5 Conditions and outstanding limitations

1. **Source-only demonstrations** (§G.4) need the lead's acceptance as the 5.1 distribution boundary.
2. **Platform coverage.** Windows 11 with CPython 3.10.8 and 3.13.7; Ubuntu 24.04.3 under WSL2 with CPython 3.12.3. No bare-metal or other Linux distribution, macOS, CPython 3.11 or 3.14, or `[replay]`/`[designer]` GUI extras were qualified. The Designer's starter selection uses the same bootstrap and registry exercised here, but it was not driven from an installed wheel.
3. **Frozen executables and the Windows installer** were not requalified. They collect `starter_agents/` directly and do not read `pyproject.toml`. Installer qualification is out of scope.
4. **CI.** No workflow changed and nothing was pushed, so the GitHub Actions `build-linux-wheel` job, red at `a1aff90` because of the retired modules, has not been observed passing. Its exact commands (`python -m build --wheel`, then `tools/check_wheel.py`) pass locally on the Linux-built wheel. The build-based pytest cases skip where setuptools>=69 is not importable, which is expected in CI's editable-install jobs. In CI the artifact protection is therefore the checker step; locally, and for release qualification via `BYTEFRAY_WHEEL`, the tests run against a real wheel.
5. **Checker trust model.** The checker imports the wheel's two registry modules in an `-I` interpreter. That is appropriate for a freshly built wheel in a trusted build environment, but it is not a sandbox against hostile site `.pth` hooks.
6. The reconciled baseline's 89 inherited full-suite failures remain unchanged (§F.1).

## H. Final Git state

Branch `v6-p1-remediation-02-wheel` in `D:\Projects\BATTLE2-worktrees\p1-remediation-02-wheel`, local commits on `a1aff90`:

| Commit | Content |
|---|---|
| `ff30490c09efa17321a351431ad718f0c74c8bde` | `fix(packaging): ship the V6 teaching agents complete in the wheel` (`pyproject.toml`, `tools/check_wheel.py`, `engine/tests/test_check_wheel.py`, `engine/tests/test_wheel_packaging.py`) |
| `f9b9da9fc7e116aeda2f2517123fcca5146633c2` | `fix(packaging): read the wheel's registries as its runtime builds them` (review correction: `tools/check_wheel.py`, both wheel test modules) |
| Branch head | `docs(release): add the Pre-RC Remediation 02 report` (this file only); its SHA is reported in the hand-off |

Changed-file inventory `a1aff90..HEAD`: `pyproject.toml`, `tools/check_wheel.py`, `engine/tests/test_check_wheel.py`, `engine/tests/test_wheel_packaging.py` (new), `docs/releases/5_1_PRE_RC_REMEDIATION_02.md` (new). No file under `engine/src`, `client/src`, `app`, `docs/v6` or the Spectator repository changed.

The worktree is clean after the report commit (`git status --porcelain` empty; evidence is under the ignored `work/`). Nothing was pushed, merged or tagged: the branch has no upstream, and the only shared-repository ref that changed is this branch. The detached helper worktrees `p1-remediation-02-full-ff30490` and `p1-remediation-02-full-a1aff90`, the review clone and the WSL directories `~/p1r02-qual-*` are disposable.

Work stops here. P2 Spectator launcher remediation and Bytefray 5.1 Alpha RC Preparation were not started and require separate authorization.
