# Bytefray V5 Alpha 1 — Phase F2

## Frozen Packaging Hygiene / Bytecode Exclusion

Date: 2026-09-09. This is a narrow remediation record for the packaging-hygiene
defect recorded as an incidental finding in
`docs/research/v5/V5_ALPHA1_PHASE_F1_TEMPLATE_PACKAGING_REMEDIATION.md`. Phase F
qualification was **not** resumed or started here, no installer/Linux work was
performed, and nothing was published.

**REMEDIATION COMPLETE — READY FOR NEW CANDIDATE COMMIT AND FULL PHASE F
REQUALIFICATION**

## A. Starting baseline

| Property | Recorded value |
| --- | --- |
| Branch | `v5-research` |
| Starting HEAD SHA | `45ccc3462cf95686846bd6c4a2f5af31869c0cdb` |
| Local `origin/v5-research` | Same SHA |
| Phase F1 remediation commit present | Yes — HEAD is `fix(packaging): include API v2 scaffold resources` |
| Product version | `5.0.0a1` (`pyproject.toml:10`), unchanged throughout |
| Starting `git status --short --untracked-files=all` | Empty |
| Starting `git diff --check` | Empty |
| `.git/index.lock` | Absent |
| `.git/index` | 93,516 bytes, modified 2026-09-09 13:12:11 local |
| Host | Windows 11 Pro, build 26120, AMD64 |
| Python | CPython 3.13.14 |
| Toolchain | pytest 9.1.1; Ruff 0.16.3; mypy 2.3.1; PyInstaller 6.22.2 |

## B. Incidental finding provenance

Phase F1 fixed the Agent API v2 scaffold omission. Its **first** remediation
build then unexpectedly bundled five stale
`__pycache__/agent.cpython-311.pyc` files from
`engine/src/battle_engine/data/starter_agents/v4_*/` into the frozen payload.
Per that phase's instruction to remove stale build output without touching
source, the ignored `__pycache__` directories were deleted by hand and the
executable was rebuilt; the artifact F1 recorded is that clean rebuild.

F1 explicitly declined to fix the underlying gap and recorded it as
"real, pre-existing, and deliberately left unfixed", recommending it as a
separate packaging-hygiene item before publication. Phase F never saw the
problem because its executable was built from a clean `git archive` export
rather than from a working tree, while `tools/build_win.ps1` builds from the
live repository root.

The mechanism is ordinary rather than exotic, which is why it recurs: the
engine imports agent modules out of `battle_engine/data` at runtime, so
CPython writes `__pycache__` beside shipped product data as a normal
consequence of running the product. This checkout already contained one such
genuine, pre-existing cache at
`engine/src/battle_engine/data/reference_agents/core_defender/__pycache__/`
(untouched by this phase; that directory is collected by no spec).

## C. Pre-fix reproduction

Reproduced deliberately **before any file was edited**.

Eight synthetic sentinels were planted across every distinct collection
surface. Each is ignored by `.gitignore` (`__pycache__/`, `*.py[cod]`,
`*.pyo`), and `git status --short --untracked-files=all` remained empty with
all eight present, confirming they introduced no tracked modification. Their
content is the literal text `PHASE-F2-SENTINEL-NOT-REAL-BYTECODE` — never a
real code object, so nothing could import or execute them. No pre-existing
file was overwritten.

| Sentinel (repository-relative) | Surface it proves |
| --- | --- |
| `engine/src/battle_engine/data/starter_agents/v5_scout_striker/__pycache__/phase_f2_sentinel.cpython-313.pyc` | nested `__pycache__` under `starter_agents` |
| `engine/src/battle_engine/data/starter_agents/hunter/phase_f2_sentinel.pyc` | loose `.pyc` outside a cache directory |
| `engine/src/battle_engine/data/starter_agents/runner/phase_f2_sentinel.pyo` | loose `.pyo` |
| `engine/src/battle_engine/data/agent_template_v2/__pycache__/phase_f2_sentinel.cpython-313.pyc` | Agent API v2 template directory (F1's fix area) |
| `engine/src/battle_engine/data/agent_template_v2_annotated/phase_f2_sentinel.pyc` | annotated API v2 template directory |
| `app/assets/branding/__pycache__/phase_f2_sentinel.cpython-313.pyc` | `bytefray.spec`'s `assets/branding` collection |
| `assets/phase_f2_sentinel.pyc` | repository-root `assets/` tree |
| `assets/branding/__pycache__/phase_f2_sentinel.cpython-313.pyc` | nested cache inside `assets/` |

Build command (the same PyInstaller invocation `tools/build_win.ps1` issues
per artifact, with output redirected to a phase-labelled directory exactly as
Phase F1 did):

```
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean \
    --workpath build\phase-f2-prefix --distpath dist\phase-f2-prefix \
    tools\bytefray.spec
```

**Leak reproduced: YES.** All eight sentinels reached a frozen payload — six
in `bytefray`, seven in `bytefray-agent-designer` (the two trees overlap on
all but `app/assets/branding` and repository-root `assets/`).

| Payload | `__pycache__` | `.pyc` | `.pyo` |
| --- | ---: | ---: | ---: |
| `dist/phase-f2-prefix/bytefray` | 3 | 5 | 1 |
| `dist/phase-f2-prefix/bytefray-agent-designer` | 3 | 6 | 1 |

Leaked locations were the collected trees verbatim, e.g.
`dist/phase-f2-prefix/bytefray/_internal/battle_engine/data/starter_agents/v5_scout_striker/__pycache__/phase_f2_sentinel.cpython-313.pyc`
and
`dist/phase-f2-prefix/bytefray-agent-designer/_internal/assets/phase_f2_sentinel.pyc`.

Every bytecode file in both pre-fix payloads was a planted sentinel: the
counts above account for all of them, so PyInstaller's own collection of
third-party packages (PySide6, pygame-ce and the rest) contributed **zero**
`.pyc` data files. That measurement is what made a narrow, repository-scoped
filter sufficient — there is no legitimate third-party bytecode to protect or
to strip.

## D. Root cause

All four shipped specs appended `(source_directory, destination)` tuples to
`datas`. PyInstaller expands such a tuple by walking the directory and
collecting **everything** beneath it, and exposes no exclusion hook at that
point. Combined with a build that runs from the live repository root, any
ignored file inside a collected tree — bytecode included — is packaged
verbatim.

The wheel and sdist never had this defect because they filter at their own
packaging boundary: `pyproject.toml`'s
`[tool.setuptools.exclude-package-data]` and `MANIFEST.in`'s
`global-exclude *.py[cod]`.

### Collection surface (full audit)

The task prompt named two specs; the repository's release build
(`tools/build_win.ps1`) defines **four** artifacts, and all four carried the
same defect. Every directory-collection path was remediated.

| Spec | Collected tree | Destination | Can hold bytecode |
| --- | --- | --- | :-: |
| `bytefray.spec` | `app/assets/branding` | `assets/branding` | yes |
| `bytefray.spec` | `.../data/starter_agents` | `battle_engine/data/starter_agents` | yes (runtime imports) |
| `bytefray.spec` | `.../data/agent_template*` ×4 | `battle_engine/data/<name>` | yes |
| `bytefray_cli.spec` | `.../data/starter_agents` | `battle_engine/data/starter_agents` | yes |
| `agent_designer.spec` | `assets/` | `assets` | yes |
| `agent_designer.spec` | `.../data/starter_agents` | `battle_engine/data/starter_agents` | yes |
| `agent_designer.spec` | `.../data/agent_template*` ×4 | `battle_engine/data/<name>` | yes |
| `replay_viewer.spec` | `assets/` | `assets` | yes |

The pMARS entries (`pmars.exe`, `COPYING`) are individual **file** tuples,
not directories, and were left unchanged — they cannot collect anything
incidental.

No hidden/ignored development file class other than Python bytecode was found
to be incidentally collected by these trees, so the exclusion scope was not
broadened.

## E. Remediation design

A single canonical helper, `tools/packaging_data.py`, is imported by all four
specs. It expands each repository directory into per-file `datas` entries
itself, dropping bytecode as it goes, so PyInstaller is never handed a
directory it would glob unfiltered. Exclusion is therefore **by
construction** rather than a cleanup applied afterwards, and it holds no
matter what the developer's checkout contains.

```python
datas += collect_data_tree(starter_agents_dir, "battle_engine/data/starter_agents")
datas += collect_data_tree(
    template_dir, f"battle_engine/data/{template_dir_name}", required=True
)
```

Two properties were deliberately preserved:

* **Optional trees stay optional.** `assets/` and the branding directory were
  previously guarded with `os.path.isdir`; `collect_data_tree` returns an
  empty list for an absent optional tree, so partial and non-Windows
  checkouts build exactly as before.
* **Phase F1's fail-loud contract is preserved and extended.** Each spec keeps
  its own precise "template resource directory is missing" `SystemExit`
  (better diagnostics than a generic message), and `required=True` adds a
  second guard F1 could not have needed: a required directory that exists but
  yields no packageable files now fails the build. Per-file collection newly
  makes "present but empty" possible, and that would reproduce F1's exact
  user-visible defect while every directory-existence check still passed.

`tools/build_win.ps1` did **not** previously depend on manually removing
caches — it cleans only its own `build\windows` / `dist\windows` output
directories — so no such dependency had to be removed. A non-destructive
post-build guard was added as defence in depth: it fails the build if any
distributable tree contains `__pycache__`, `.pyc` or `.pyo`. It deliberately
deletes nothing from the checkout, because a build that is correct only after
a sweep is precisely the property this phase removed. No `git clean` is used
anywhere.

## F. Filtering contract

Excluded, matched as paths rather than as text:

```
__pycache__/     (any path component -- the whole cache subtree)
*.pyc            (case-insensitive suffix)
*.pyo            (case-insensitive suffix)
```

* Version-agnostic: `cpython-311`, `cpython-313`, `cpython-314` and any future
  tag are excluded by the same unchanged rule. No interpreter version string
  appears in the filter.
* Separator-agnostic: implemented with `pathlib`, so
  `nested/__pycache__/x.pyc` and `nested\__pycache__\x.pyc` are treated
  identically. A substring rule such as `"/__pycache__/" in text` would have
  silently stopped filtering on the very platform that ships these artifacts.
* Destinations are emitted with `/` separators, matching PyInstaller's
  convention and the literal destinations the specs already used.

**`.pyd` is deliberately NOT excluded.** It matches setuptools' `*.py[cod]`
shorthand but is a native Windows extension module — compiled C, not a
bytecode cache — and stripping it would break the frozen application. The
frozen rule is intentionally narrower than the wheel's.

## G. Regression coverage

New: `engine/tests/test_frozen_bytecode_exclusion.py` (46 tests).

| Layer | Coverage |
| --- | --- |
| Filtering rule (unit) | Allowed vs rejected paths, nested paths, Windows/POSIX agreement, version-independence, `.pyd` preserved, `__pycache__.txt`/`pycache_notes.md` not misidentified |
| `collect_data_tree` (unit) | Dirty synthetic tree in → clean per-file entries out; sources real and contained; POSIX destinations; root-file placement; optional-missing skips; required-missing raises; required-but-bytecode-only raises |
| Synthetic dirty checkout | Plants real ignored bytecode in the **real** collected trees, executes the **real** `.spec` files over it, asserts zero sentinels and zero bytecode in `datas` for **all four** specs, and separately asserts the legitimate neighbours still package |
| Built artifact | Walks an actual onedir distribution and asserts zero `__pycache__`/`.pyc`/`.pyo`, gated on `BYTEFRAY_FROZEN_EXE` (shared with the F1 frozen gate) |

The dirty-checkout fixture mutates the working checkout rather than a copy,
because the defect is a property of building *from a checkout*; a temporary
directory would exercise a path no release build takes. Every planted file is
gitignored, uniquely named, and removed in teardown along with any directory
the fixture created.

`engine/tests/test_windows_packaging_spec.py` was updated for the new
collection shape. Its assertions moved from "a tuple naming this directory is
present" to "these exact files land at these exact frozen destinations" —
strictly stronger, since the old form only proved the spec *mentioned* a
resource. One test was added pinning the build script's guard and its
non-destructiveness.

### Negative controls (§29)

Both were run without editing any repository file and without any Git
mutation, and the repository was not left in a defective state.

**A — exclusion neutralised at runtime.** A scratch pytest plugin rebound
`tools.packaging_data.is_python_bytecode` to always return `False`, restoring
pre-fix behaviour. All four `test_dirty_checkout_produces_a_clean_data_list`
cases **failed**, each naming the planted sentinels it had collected, e.g.
`replay_viewer.spec collected planted bytecode sentinels: [...dirty_34fe3622.cpython-313.pyc, ...dirty_34fe3622.pyc, ...dirty_34fe3622.pyo]`.

**B — deliberately contaminated payload.** A synthetic distribution
containing `_internal/.../__pycache__/agent.cpython-313.pyc` was pointed at by
`BYTEFRAY_FROZEN_EXE`; `test_frozen_payload_contains_no_python_bytecode`
**failed**. Removing only that cache directory made the same test pass,
confirming the failure was caused by the contamination and not by the
harness.

The new coverage is therefore demonstrably capable of detecting the class of
defect it claims to prevent.

## H. Dirty-build proof

The post-fix build was made **deliberately dirty**: all eight sentinels from
section C were recreated and **not** cleaned, and their presence was verified
immediately before the build ran and again immediately after it finished. All
four artifacts were built from that dirty checkout.

| Artifact | Exit | Elapsed |
| --- | ---: | ---: |
| `bytefray` | 0 | 35 s |
| `bytefray-cli` | 0 | 10 s |
| `bytefray-agent-designer` | 0 | 32 s |
| `bytefray-replay-viewer` | 0 | 13 s |

This proves safe packaging *despite* a dirty source tree, not safe packaging
*after* cleanup.

`tools/build_win.ps1` itself was not executed end to end: it begins with
`pip install --upgrade pip wheel` and `pip install -e .`, which would mutate
the environment mid-qualification, and it wipes `dist\windows`. Its
per-artifact PyInstaller invocation was reproduced verbatim into
phase-labelled directories instead — the same approach Phase F1 took. The
guard block added to that script was exercised directly against both payload
sets: it **throws** on the pre-fix trees (9 and 10 debris items) and
**passes** on all four F2 trees.

## I. Frozen payload result

From the deliberately dirty build:

| Artifact | `__pycache__` | `.pyc` | `.pyo` | Sentinels |
| --- | ---: | ---: | ---: | ---: |
| `bytefray` | **0** | **0** | **0** | **0** |
| `bytefray-cli` | **0** | **0** | **0** | **0** |
| `bytefray-agent-designer` | **0** | **0** | **0** | **0** |
| `bytefray-replay-viewer` | **0** | **0** | **0** | **0** |

All eight synthetic sentinels are absent from every payload while remaining
present in the source tree throughout the build.

### Payload comparison

Pre-fix and F2 payloads were compared by file inventory. The **only**
difference is the removal of bytecode debris; nothing was added, and no
legitimate product file was removed.

| Artifact | Before | After | Removed | Added |
| --- | ---: | ---: | ---: | ---: |
| `bytefray` | 292 | 286 | 6 (all sentinels) | 0 |
| `bytefray-agent-designer` | 294 | 287 | 7 (all sentinels) | 0 |

No payload difference beyond bytecode filtering was observed.

## J. Required-resource preservation

Verified against the same deliberately dirty build.

| Resource | Present |
| --- | :-: |
| API-v1 blank scaffold (`agent_template`) | yes (`agent.py` + `agent.yaml`) |
| API-v1 annotated (`agent_template_annotated`) | yes |
| API-v2 blank (`agent_template_v2`) | yes |
| API-v2 annotated (`agent_template_v2_annotated`) | yes |
| V5 starter directories | all four (`v5_core_defender`, `v5_dual_team`, `v5_region_attacker`, `v5_scout_striker`) |
| Starter directories total | 21 in payload / 21 in source |
| Starter manifests (`agent.yaml`) | 21 |
| Designer branding icon | yes |
| pMARS Windows backend | yes |
| Designer payload scaffold templates | all four |

`v5_scout_striker` is the sharpest case: it carried a `__pycache__` sentinel
in source, and both of its legitimate files survived while the cache did not.
Collection fidelity was also checked directly — the source tree holds 39
non-bytecode files under `starter_agents` and the helper emits exactly 39
entries.

## K. Functional smoke

Against `dist/phase-f2-remediation/bytefray/bytefray.exe`, from a temporary
directory outside the repository, with `PYTHONPATH` removed and an isolated
`BYTEFRAY_ROOT` — so no repository-local fallback could mask a missing
resource.

| Check | Exit | Result |
| --- | ---: | --- |
| `--version` | 0 | `Bytefray 5.0.0a1, Agent API v2, result schema v1, replay schema v4, Python 3.13.14` |
| `agents` (listing) | 0 | 25 lines, starters discovered |
| API-v1 blank create / validate | 0 / 0 | — |
| API-v1 annotated create / validate | 0 / 0 | — |
| API-v2 blank create / validate | 0 / 0 | — |
| API-v2 annotated create / validate | 0 / 0 | — |

A first attempt used `agents list`, which exits 2 because the listing is the
bare `agents` subcommand and takes no arguments. That was a harness mistake,
not product behaviour; it is recorded rather than hidden, and the corrected
invocation produced the row above.

## L. Phase F1 non-regression

Both Agent API v2 scaffolds were not merely created and validated but **run to
completion as real matches from the frozen executable**, reproducing Phase
F1's recorded outcomes exactly.

| Variant | Create | Validate | Real match (vs `v4_scout`, seed 1234) | F1 recorded |
| --- | ---: | ---: | --- | --- |
| API-v2 blank | 0 | 0 | exit 0, `bytefray-rules-4`, **tie** | tie ✓ |
| API-v2 annotated | 0 | 0 | exit 0, `bytefray-rules-4`, **winner A** | winner A ✓ |

Both produced `result.json`, `replay.jsonl` and `summary.json`. Phase F1's
frozen scaffold gate passes against this executable.

## M. Wheel/sdist disposition

**Unchanged — and confirmed empirically, not merely by reading config.** A
wheel and sdist were built from a deliberately dirty tree carrying
`starter_agents/hunter/__pycache__/wheelprobe.cpython-313.pyc` and
`agent_template_v2/wheelprobe.pyc`:

| Distribution | Entries | Bytecode/cache | Probes |
| --- | ---: | ---: | ---: |
| `bytefray-5.0.0a1-py3-none-any.whl` | 204 | **0** | **0** |
| `bytefray-5.0.0a1.tar.gz` | 295 | **0** | **0** |

Both Agent API v2 template files are present in the wheel. `pyproject.toml`
was not modified; no change is warranted. The F2 helper is used only by the
`.spec` files and plays no part in setuptools packaging.

## N. Artifact inventory

**PHASE F2 REMEDIATION PROOF ARTIFACTS — NOT PUBLICATION-QUALIFIED.**

These were built from a working tree whose changes are uncommitted, and from a
deliberately dirty checkout. They exist to prove the fix, not to ship.

| Artifact | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `dist/phase-f2-remediation/bytefray/bytefray.exe` | 4,072,028 | `1682D518D546E881AA6AC8B898D8FE677C352A80561BC390FE3C1234F8645746` |
| `dist/phase-f2-remediation/bytefray-cli/bytefray-cli.exe` | 2,767,002 | `728392F9DC4FFC0D0D00E8F4A974ADAB6C437FBEA096D41D24E116BAC9E8525D` |
| `dist/phase-f2-remediation/bytefray-agent-designer/bytefray-agent-designer.exe` | 4,065,707 | `EEB2DBC941949C1D7E053DB4F5C3D6AAA5C52CD06C22FBA1DCA1CE63BB2D2E7F` |
| `dist/phase-f2-remediation/bytefray-replay-viewer/bytefray-replay-viewer.exe` | 3,825,963 | `E033A78E04081E910EAB937EA9F0817A3262FB7B21BD67BDEAFAB50444BC5298` |

Prior artifacts are unchanged historical evidence: the blocked Phase F
candidate artifacts remain **NOT APPROVED**, and the Phase F1 artifact remains
**remediation proof only**. No historical report was rewritten. Complete
Phase F must rebuild fresh artifacts from the eventual committed SHA.

## O. Regression validation

| Gate | Result |
| --- | --- |
| `python -m pytest` (full default suite) | **3343 passed, 21 skipped, 3 deselected** in 369.05 s |
| `ruff check .` | All checks passed |
| `mypy engine/src/battle_engine` | Success: no issues in 107 source files |
| `mypy client/src/battle_client` | Success: no issues in 16 source files |
| Stable V4 equivalence group | 84 passed |
| V4 placement/scheduler stable group | 85 passed |
| Phase B R1/R2 engine hygiene | 8 passed |
| V5 starter qualification gate | 78 passed |
| Focused packaging/scaffold selection (`BYTEFRAY_FROZEN_EXE` set) | 139 passed, 0 skipped |

No golden fixture changed.

**Count reconciliation.** Phase F1 recorded 3303 passed / 14 skipped with
`BYTEFRAY_FROZEN_EXE` set. Without that variable its six frozen-artifact tests
skip, giving a 3297 / 20 baseline. F2 adds 47 tests (46 in the new module, 1
build-script guard), of which 46 run by default and 1 skips without the
variable: 3297 + 46 = **3343 passed**, 20 + 1 = **21 skipped**, deselected
unchanged at 3. Every count is accounted for; no pre-existing test changed
status.

**One transient failure is recorded rather than hidden.** An intermediate full
run, executed while the eight sentinels were still planted, reported 4 failed
/ 3339 passed: two starter-digest tests and two frozen-population tests
detected the loose `.pyc`/`.pyo` sentinels inside `starter_agents/hunter` and
`starter_agents/runner`. Those failures were caused by the deliberate test
debris, not by the F2 change — after removing only the task-created sentinels,
the same four tests pass (26 passed in that selection) and the full suite is
green as tabulated above.

That diagnosis surfaced a genuine, pre-existing asymmetry worth recording
without acting on it: `battle_engine.starters.starter_content_files` excludes
`__pycache__` directories but not a loose `.pyc`/`.pyo` sitting directly
beside `agent.py`. Realistic CPython output always lands in `__pycache__`,
which that function already handles — which is exactly why the
`v5_scout_striker` cache sentinel changed no digest while the two loose ones
did. The F2 packaging filter is strictly broader than that runtime rule.
This is **not** a blocker and is deliberately out of scope per the phase's
instruction not to broaden remediation without strong evidence; it is flagged
here for a future hygiene pass.

## P. Semantic impact

| Area | Changed |
| --- | :-: |
| Gameplay mechanics | **NO** |
| Ruleset behaviour | **NO** |
| Agent API behaviour | **NO** |
| Starter behaviour | **NO** |
| Parameter semantics | **NO** |
| Designer UX/behaviour | **NO** |
| Replay schema | **NO** |
| Result schema | **NO** |
| Product version | **NO** — remains `5.0.0a1` |
| Starter / Agent API versions | **NO** |
| Wheel / sdist contents | **NO** |

No file under `engine/src/battle_engine/` or `client/src/battle_client/` was
modified. `rules.py`, `ruleset_policy.py`, `process_runtime.py`,
`scheduler.py`, `scoring.py` and `vm.py` are untouched. The change is confined
to packaging inputs and their tests.

### Files changed

| File | Status |
| --- | --- |
| `tools/packaging_data.py` | **added** — canonical filtered collector |
| `engine/tests/test_frozen_bytecode_exclusion.py` | **added** — 46 tests |
| `tools/bytefray.spec` | modified |
| `tools/bytefray_cli.spec` | modified |
| `tools/agent_designer.spec` | modified |
| `tools/replay_viewer.spec` | modified |
| `tools/build_win.ps1` | modified — non-destructive post-build guard |
| `engine/tests/test_windows_packaging_spec.py` | modified — destination-path assertions, +1 guard test |

Nothing was deleted.

## Q. Repository health

| Check | Result |
| --- | --- |
| `git status --short --untracked-files=all` | Exactly the eight files above; nothing unrelated |
| `git diff --stat` | 6 files changed, 179 insertions(+), 84 deletions(-) |
| `git diff --check` | Clean |
| `.git/index.lock` | Absent |
| `.git/index` | 93,516 bytes — byte-identical to the starting value |
| Git mutation commands run | **None** |
| Task-created sentinel debris | Removed (8 files, 4 directories) |
| Pre-existing caches | Preserved untouched |
| Publication actions | **None** |

All task-created processes terminated. One qualification note: the frozen
replay viewer was included in a GUI startup smoke by mistake and did not
self-exit, because only `app/agent_designer.py` implements the
`BYTEFRAY_GUI_SMOKE_EXIT_MS` hook — which is precisely why
`tools/build_win.ps1` smokes only the Designer and `bytefray design`. The
process was identified as task-created by its path under
`dist/phase-f2-remediation/` and terminated; no unrelated process was
affected. The reported exit code `-1` for that one entry is that termination,
not a product fault.

## R. Verdict

**REMEDIATION COMPLETE — READY FOR NEW CANDIDATE COMMIT AND FULL PHASE F
REQUALIFICATION**

Phase F requalification was not started here and must not be inferred from
this record. The next action is the user staging, committing and pushing the
F2 remediation, producing a new candidate SHA, after which **complete** Phase F
qualification begins from the beginning against freshly built artifacts.
