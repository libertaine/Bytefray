# Bytefray V5 Alpha 1 — Phase F1

## Frozen API-v2 Scaffold Packaging Remediation

Date: 2026-09-09. This is a narrow remediation record for the single
publication blocker recorded in
`docs/research/v5/V5_ALPHA1_PHASE_F_QUALIFICATION.md`. Phase F qualification
was **not** resumed here, no installer/Linux/publication work was performed,
and nothing was published.

**REMEDIATION COMPLETE — READY FOR NEW CANDIDATE COMMIT AND FULL PHASE F
REQUALIFICATION**

## A. Starting baseline

| Property | Recorded value |
| --- | --- |
| Branch | `v5-research` |
| Starting HEAD SHA | `bfccd6aeb36b554d0a33581b3da117812b8dbbb1` |
| Local `origin/v5-research` | Same SHA |
| Blocked candidate | `0dde69c9695c8c730fe190af23f6d92783072ffd` |
| Blocked Phase F report committed | Yes, at HEAD (`docs(v5): record alpha1 qualification block`) |
| Product version | `5.0.0a1` (`pyproject.toml:10`), unchanged throughout |
| Starting `git status --short --untracked-files=all` | Empty |
| Starting `git diff --check` | Empty |
| `.git/index.lock` | Absent |
| `.git/index` | 93,268 bytes, modified 2026-09-09 12:27:17 local |
| Host | Windows 11 Pro, build 26120, AMD64 |
| Python | CPython 3.13.14 |
| Toolchain | pytest 9.1.1; Ruff 0.16.3; mypy 2.3.1; PyInstaller 6.22.2 |

`git diff --stat 0dde69c..HEAD` is a single file, 418 insertions: the Phase F
report itself. **HEAD's product source is byte-identical to the blocked
candidate's**, so artifacts built from the candidate remain valid reproduction
evidence for HEAD.

## B. Reproduction before any edit

All three environments were exercised before a single file was modified, each
from a temporary working directory outside the repository with `PYTHONPATH`
removed and an isolated `BYTEFRAY_ROOT`, so repository files could not mask
missing packaged data.

### B1. Source checkout — control

`.venv\Scripts\python.exe -m battle_engine agents create ...`

| Variant | Exit |
| --- | ---: |
| API-v1 blank | 0 |
| API-v1 annotated | 0 |
| API-v2 blank | 0 |
| API-v2 annotated | 0 |

A first attempt used `python -m battle_engine.command`, which exits 0 without
running because that module has no `__main__` guard. That was a harness
mistake, not product behavior; it is recorded rather than hidden, and the
corrected entry point (`-m battle_engine`) produced the table above.

### B2. Clean installed wheel — control

A wheel was built from the working tree
(`bytefray-5.0.0a1-py3-none-any.whl`, 970,470 bytes, SHA-256
`91a932235d68cdb444c53654ecc5bcf45fa23652391147363d9c3616a87faa56`) and
installed into a fresh venv outside the repository. Imports resolved from that
venv's `Lib\site-packages`.

| Variant | Create | Validate |
| --- | ---: | ---: |
| API-v1 blank | 0 | 0 |
| API-v1 annotated | 0 | 0 |
| API-v2 blank | 0 | 0 |
| API-v2 annotated | 0 | 0 |

Direct archive inspection confirmed all four template directories were already
present in the wheel (two files each).

### B3. Frozen executable — defect reproduced

Against the blocked candidate's own executable
(`dist/phase-f-0dde69c-20260909/windows/bytefray/bytefray.exe`):

| Control | Exit | Result |
| --- | ---: | --- |
| `--version` | 0 | `Bytefray 5.0.0a1, Agent API v2, result schema v1, replay schema v4` |
| API-v1 blank creation | 0 | Both scaffold files written |
| API-v1 annotated creation | 0 | Both scaffold files written |
| API-v2 blank creation | **2** | `ERROR: Agent template resource directory not found. Checked: ...\_internal\battle_engine\data\agent_template_v2, ...\_internal\engine\src\battle_engine\data\agent_template_v2` |
| API-v2 annotated creation | **2** | Same error for `agent_template_v2_annotated` |

The frozen payload's `_internal\battle_engine\data` contained exactly
`agent_template`, `agent_template_annotated` and `starter_agents`.

**Frozen defect reproduced: YES**, for both API-v2 templates, before editing.

## C. Root cause

`tools/bytefray.spec` and `tools/agent_designer.spec` built their PyInstaller
`datas` lists by **enumerating scaffold template directories under hardcoded
literal names**:

```python
agent_template_dir = os.path.join(engine_src, "battle_engine", "data", "agent_template")
agent_template_annotated_dir = os.path.join(
    engine_src, "battle_engine", "data", "agent_template_annotated"
)
...
if os.path.isdir(agent_template_dir):
    datas.append((agent_template_dir, "battle_engine/data/agent_template"))
if os.path.isdir(agent_template_annotated_dir):
    datas.append((agent_template_annotated_dir, "battle_engine/data/agent_template_annotated"))
```

That list is a **second, hand-maintained copy** of an inventory the product
already defines in
`battle_engine.agent_scaffold.TEMPLATE_DIRECTORIES_BY_API_VERSION`. When the
Agent API v2 template pair was added to that dictionary, neither spec was
updated, so `agent_template_v2` and `agent_template_v2_annotated` were never
appended to `datas` and never reached the frozen `_MEIPASS`/`_internal` tree.

Classification: **PyInstaller data omission** (a build-specification
omission). It is not a resource-discovery mismatch, not a path-resolution bug,
and no runtime lookup code was at fault — `template_resource_dir` correctly
reported that a genuinely absent directory was absent.

This is the **third instance of one recurring defect class**, not a new one.
`engine/tests/test_windows_packaging_spec.py`'s own docstrings record the
prior two: `agent_template` itself shipped missing, then
`agent_template_annotated` shipped missing. Each was closed with a test
pinning that one literal directory name, so the class survived and reproduced
itself the moment a fourth template directory appeared.

### Why the wheel worked and the frozen executable did not

| Surface | Inventory mechanism | Maintenance | Outcome |
| --- | --- | --- | --- |
| Wheel / sdist | `pyproject.toml` `[tool.setuptools.package-data]` `battle_engine = ["data/**/*"]` | **Automatic glob** — no per-directory entry | All four templates shipped |
| Frozen executable | `datas` list in each `.spec`, literal names | **Manual** | Only the two v1 templates shipped |

The two surfaces disagreed because only one of them required a human to
remember. Source checkouts were never affected because
`template_resource_dir`'s second candidate resolves the real
`engine/src/battle_engine/data/<dir>` tree directly.

## D. Resource architecture

`battle_engine.agent_scaffold.template_resource_dir(resource_root, template,
api_version=...)` selects a directory name from
`TEMPLATE_DIRECTORIES_BY_API_VERSION` and probes, in order:

1. `<resource_root>/battle_engine/data/<dir_name>`
2. `<resource_root>/engine/src/battle_engine/data/<dir_name>`

`battle_engine.paths.get_resource_root()` supplies the root per environment:

| Environment | Resource root | Candidate that resolves |
| --- | --- | --- |
| Source checkout / editable install | Repository root | Second (`engine/src/...`) |
| Installed wheel | `.../site-packages` | First |
| Frozen application | `sys._MEIPASS` (PyInstaller 6 onedir: `<exe dir>\_internal`) | First |

Template directory names, derived from source (not from any prompt):

| Agent API | `blank` | `annotated` |
| ---: | --- | --- |
| 1 | `agent_template` | `agent_template_annotated` |
| 2 | `agent_template_v2` | `agent_template_v2_annotated` |

Only two shipped commands reach this resource family: `bytefray agents
create` (via `battle_engine.command._agents`) and the Agent Designer's
in-process "New Agent" dialog (`app/views/development.py`).
`battle_engine.agent_test` also loads the API-v1 blank template as its
internal reference opponent.

Audited and deliberately unchanged: `tools/bytefray_cli.spec` and
`tools/replay_viewer.spec` bundle no template. `bytefray-cli`'s parser
exposes no `agents` subcommand and the replay viewer only reads replays, so
neither can reach `agent_scaffold`; adding the resource would be dead weight.

Also verified during the trace: `battle_engine.reference_agents` and
`battle_engine.benchmarks` resolve their own `battle_engine/data/*`
directories, which are likewise absent from the frozen payload — but **no
shipped product code imports either module** (they are used by tests and
research harnesses only), so no user-facing command depends on them. No
adjacent frozen defect was found. This is recorded as a checked negative, and
no change was made for it.

## E. Fix

Both scaffold-capable specs now **derive** the template list from the
product's own canonical inventory instead of restating it:

```python
if engine_src not in sys.path:
    sys.path.insert(0, engine_src)
from battle_engine.agent_scaffold import TEMPLATE_DIRECTORIES_BY_API_VERSION

agent_template_dirs = sorted(
    {
        directory
        for templates in TEMPLATE_DIRECTORIES_BY_API_VERSION.values()
        for directory in templates.values()
    }
)
...
for template_dir_name in agent_template_dirs:
    template_dir = os.path.join(engine_src, "battle_engine", "data", template_dir_name)
    if not os.path.isdir(template_dir):
        raise SystemExit(...)
    datas.append((template_dir, f"battle_engine/data/{template_dir_name}"))
```

This gives the frozen build the same property the wheel already had: one
canonical resource set, no second inventory to maintain, and a future template
or Agent API generation packaged automatically. The former silent
`if os.path.isdir(...)` skip is replaced by a loud build failure, so a missing
required resource can no longer produce a quietly broken executable.

`battle_engine.agent_scaffold` imports only the standard library plus
`battle_engine.agent_api`/`battle_engine.paths`, and `battle_engine/__init__.py`
is import-free, so the spec-time import is cheap and side-effect free.

### Files changed

| File | Change |
| --- | --- |
| `tools/bytefray.spec` | Template `datas` derived from the canonical inventory; loud failure on a missing directory |
| `tools/agent_designer.spec` | Same derivation (added `import sys`) |
| `tools/build_win.ps1` | Frozen `agents create` smoke extended to every supported variant plus API-v2 validation |
| `engine/tests/test_windows_packaging_spec.py` | Added inventory-derived spec coverage (+8 tests) |
| `engine/tests/test_frozen_scaffold_resources.py` | **New** — product resource contract and frozen-artifact smoke |

Files deleted: none. No runtime lookup code, no product module, and no
gameplay file was touched.

## F. Regression coverage

The reason the existing 17 packaging tests and the whole scaffold suite were
green while the executable was broken is structural:
`engine/tests/test_agent_scaffold.py` passes an explicit `resource_root=ROOT`
into every call, pinning lookups to the repository source tree, so it can
never observe what a built artifact contains. The new coverage deliberately
inverts that.

**`engine/tests/test_frozen_scaffold_resources.py`** (new, 16 tests):

- *Resource inventory contract* — every supported `(api_version, template)`
  pair resolves through the **real** `get_resource_root()`, with nothing
  injected, and both template files exist. The same assertion therefore covers
  a source checkout, an installed wheel, or a frozen application, depending on
  which artifact the suite runs from. It asserts nothing about `.spec` text.
- *Real creation* — each variant is created with no injected resource root and
  taken through the normal discovery and `load_python_agent` path.
- *Frozen-artifact smoke* — opt-in via `BYTEFRAY_FROZEN_EXE`; runs the built
  executable out of process from a temporary directory with `PYTHONPATH`
  removed, asserting exit 0 for creation **and** `agents validate` for every
  supported variant, plus a payload inventory check and a guard proving the
  configured binary is not inside the repository source tree.

**`engine/tests/test_windows_packaging_spec.py`** (+8 tests): a test
parameterized over the canonical inventory × the two scaffold-capable specs,
so a template that exists in the product but in no spec fails immediately.
This closes the defect *class* rather than adding a fourth literal-name pin.

**`tools/build_win.ps1`**: the canonical Windows build's own smoke previously
created a single API-v1 agent. It now exercises every supported
`(api-version, template)` pair and validates both API-v2 results, so the
build itself fails on this defect class.

### Both new layers were proven to catch the real defect

Frozen coverage, run against the **pre-fix** candidate executable:

```text
FAILED test_frozen_executable_creates_every_supported_variant[api2-annotated]
FAILED test_frozen_executable_creates_every_supported_variant[api2-blank]
FAILED test_frozen_executable_bundles_every_supported_template_directory
  AssertionError: the frozen payload at ...\_internal\battle_engine\data is
  missing scaffold template directories
  ['agent_template_v2', 'agent_template_v2_annotated']
```

The API-v1 rows passed in the same run, reproducing the shipped defect exactly.

Spec coverage, with `tools/bytefray.spec` temporarily mutated back to the
pre-fix literal v1-only list:

```text
FAILED test_every_supported_scaffold_template_reaches_the_frozen_tree[agent_template_v2-bytefray]
FAILED test_every_supported_scaffold_template_reaches_the_frozen_tree[agent_template_v2_annotated-bytefray]
```

The spec was restored immediately afterwards and its SHA-256 re-verified
(`5635f46adb069ae05753c4a117449cb91ca699ce6831a46d65d70dc90020f267`).

## G. Post-fix proof

### Frozen executable (remediation artifact)

Run from a clean temporary directory, `PYTHONPATH` removed, isolated
`BYTEFRAY_ROOT`:

| Variant | Create | Validate | Real match |
| --- | ---: | ---: | --- |
| API-v1 blank | 0 | 0 | — |
| API-v1 annotated | 0 | 0 | — |
| API-v2 blank | **0** | **0** | vs `v4_scout`, seed 1234 → exit 0, `bytefray-rules-4`, tie |
| API-v2 annotated | **0** | **0** | vs `v4_scout`, seed 1234 → exit 0, `bytefray-rules-4`, winner A |

Both API-v2 scaffolds were not merely created and validated but **run to
completion as real matches from the frozen executable**, producing result,
replay and summary artifacts.

The frozen test suite passes against this executable: **16 passed, 0 skipped**.

### Installed wheel

`get_resource_root()` in the clean venv resolves to that venv's
`Lib\site-packages`, and both API-v2 templates resolve beneath it — no source
checkout fallback.

| Variant | Create | Validate |
| --- | ---: | ---: |
| API-v1 blank | 0 | 0 |
| API-v1 annotated | 0 | 0 |
| API-v2 blank | 0 | 0 |
| API-v2 annotated | 0 | 0 |

### Resource parity invariant

| Environment | v1 blank | v1 annotated | v2 blank | v2 annotated |
| --- | :-: | :-: | :-: | :-: |
| Source checkout | ✓ | ✓ | ✓ | ✓ |
| Installed wheel | ✓ | ✓ | ✓ | ✓ |
| Frozen executable | ✓ | ✓ | ✓ | ✓ |

### Template contents unchanged

All eight template files hash identically to their pre-edit fingerprints, in
both the source tree and the frozen payload:

| Directory | `agent.yaml` | `agent.py` |
| --- | --- | --- |
| `agent_template` | `05a38adc…4103` | `9174c697…be57` |
| `agent_template_annotated` | `05a38adc…4103` | `a55197d2…ff6b9` |
| `agent_template_v2` | `4f2e440d…a176` | `8db2de1f…6c76f4` |
| `agent_template_v2_annotated` | `4f2e440d…a176` | `a317e825…e4cf4` |

**Template contents changed: NO.**

## H. Remediation artifact

Built with the unchanged canonical spec and the same PyInstaller command
structure `tools/build_win.ps1` uses, into fresh isolated work/dist paths. No
`git clean` was used; stale output was isolated in new directories rather than
deleted from the repository.

```powershell
# Working directory: D:\Projects\BATTLE2
& '.\.venv\Scripts\python.exe' -m PyInstaller --noconfirm --clean `
    --workpath 'build\phase-f1-remediation\pyinstaller' `
    --distpath 'dist\phase-f1-remediation\windows' `
    tools\bytefray.spec
```

| Property | Value |
| --- | --- |
| Base HEAD SHA | `bfccd6aeb36b554d0a33581b3da117812b8dbbb1` |
| Working-tree state | **Dirty** — 4 modified/added files, uncommitted |
| Product version | `5.0.0a1` |
| Python | CPython 3.13.14 |
| PyInstaller | 6.22.2 |
| Filename | `dist/phase-f1-remediation/windows/bytefray/bytefray.exe` |
| Size | 4,072,028 bytes |
| SHA-256 | `33709101afbec4a4cd8b2c4a0b61eceb9124b7e946f6f4f1d268966f819c7823` |
| Onedir payload | 286 files, 132,968,681 bytes |
| Build interval | 2026-09-09 16:42:51–16:43:27 UTC |

The standalone Designer was also rebuilt, because its spec changed:

| Property | Value |
| --- | --- |
| Filename | `dist/phase-f1-remediation/windows-designer/bytefray-agent-designer/bytefray-agent-designer.exe` |
| Size | 4,065,707 bytes |
| SHA-256 | `a375ada80fccf3a9b0516f6237fa041dc514c5c0c5abde5357b652c4014990de` |
| Onedir payload | 287 files, 134,286,257 bytes |
| Frozen template inventory | All four directories present |

This proves the changed Designer spec still builds and now carries the same
resource set. Frozen Designer GUI behaviour was **not** exercised; that belongs
to full Phase F requalification.

### Payload diff against the blocked candidate

The remediation payload differs from the blocked candidate's payload by
**exactly four files, all additions, nothing removed**:

```text
+ _internal\battle_engine\data\agent_template_v2\agent.py
+ _internal\battle_engine\data\agent_template_v2\agent.yaml
+ _internal\battle_engine\data\agent_template_v2_annotated\agent.py
+ _internal\battle_engine\data\agent_template_v2_annotated\agent.yaml
```

282 → 286 files; 132,962,649 → 132,968,681 bytes (+6,032). This is the
strongest available evidence that the change is a pure resource-availability
fix.

**NOT PUBLICATION-QUALIFIED.** These artifacts were built from a dirty working
tree whose remediation changes are not yet committed. They exist to prove the
fix, not to ship. Complete Phase F requalification must produce fresh
artifacts and hashes from the new committed SHA.

### Incidental finding — stale bytecode contamination (not fixed here)

The **first** remediation build unexpectedly bundled five stale
`__pycache__/agent.cpython-311.pyc` files from
`engine/src/battle_engine/data/starter_agents/v4_*/` into the frozen payload.
The cause is that `tools/build_win.ps1` builds from the live repository root
and the specs collect whole directories, while the wheel and sdist both filter
bytecode explicitly (`[tool.setuptools.exclude-package-data]` and
`MANIFEST.in`'s `global-exclude *.py[cod]`). Phase F never saw this because it
built from a clean `git archive` export.

Per this phase's instruction to remove stale build output without touching
source, the six ignored, untracked `__pycache__` directories under
`engine/src/battle_engine/data/` were deleted and the executable was rebuilt;
the artifact recorded above is the clean rebuild and contains no bytecode.

The underlying gap — the PyInstaller specs have no bytecode filter, so a
release build from a working tree that happens to contain caches would ship
foreign `.pyc` files — is **real, pre-existing, and deliberately left
unfixed** as outside this narrow phase's scope. Fixing it means changing how
`datas` collects directories, which would alter the frozen payload beyond the
remediation and needs its own qualification. Recommended as a separate
packaging-hygiene item before publication.

## I. Regression validation

| Gate | Result |
| --- | --- |
| `python -m pytest` (full default suite) | **3303 passed, 14 skipped, 3 deselected** in 378.85s |
| `ruff check .` | All checks passed |
| `mypy engine/src/battle_engine` | Success: no issues in 107 source files |
| `mypy client/src/battle_client` | Success: no issues in 16 source files |
| Stable V4 equivalence group | 84 passed |
| Phase B R1/R2 engine hygiene | 8 passed |
| V5 starter qualification gate | 78 passed |
| V4 placement/scheduler stable group | 85 passed |
| Focused scaffold/resource/validation selection | 324 passed, 6 skipped |

The full-suite total rose from Phase F's 3279 to 3303: **+24, exactly the new
tests** (16 new frozen-resource tests, 8 new packaging-spec tests). Skipped
(14) and deselected (3) are unchanged from the Phase F baseline. The full run
was executed with `BYTEFRAY_FROZEN_EXE` set, so all six frozen-artifact tests
ran rather than skipping. In the focused selection that variable was unset,
which is why six show as skipped there — that is the intended default for a
suite with no build available.

Named gate counts match the Phase F baseline exactly (V4 equivalence 23 + 2 +
10 + 49 = 84; hygiene 8; V5 starters 54 + 24 = 78; placement/scheduler 67 + 18
= 85). No golden fixture was changed.

## J. Semantic impact

| Surface | Changed |
| --- | --- |
| Gameplay semantics | **NO** |
| Stable ruleset behavior | **NO** |
| Starter behavior | **NO** |
| Agent API v2 semantics | **NO** |
| Parameter semantics | **NO** |
| Designer behavior | **NO** |
| Replay schema | **NO** |
| Product version | **NO** — remains `5.0.0a1` |
| Scaffold template contents | **NO** — all eight files hash-identical |

No file under `engine/src/` or `client/src/` or `app/` was modified. The
changed set is two PyInstaller specs, one build script, and test code.

**Remediation classification: PACKAGING-ONLY / AUTHORING-RESOURCE
AVAILABILITY FIX.**

## K. Repository health

Final state after all commands, builds and test runs terminated:

```text
 M engine/tests/test_windows_packaging_spec.py
 M tools/agent_designer.spec
 M tools/build_win.ps1
 M tools/bytefray.spec
?? docs/research/v5/V5_ALPHA1_PHASE_F1_TEMPLATE_PACKAGING_REMEDIATION.md
?? engine/tests/test_frozen_scaffold_resources.py
```

`git diff --stat` on tracked files: 4 files changed, 168 insertions(+), 33
deletions(-). This report is the fifth tracked-scope addition and, like the
Phase F report before it, is **not part of any candidate SHA** until the user
commits it.

`git diff --check` empty. `.git/index.lock` absent. `.git/index` 93,268 bytes
with its original modification time — no Git mutation command was run at any
point. All Git inspection used `git --no-optional-locks`. No detached or
background process was launched; every build and test invocation was awaited.

The only additions outside tracked scope are ignored build/dist output
(`build/phase-f1-remediation/`, `dist/phase-f1-remediation/`) and the isolated
temporary environments used for the proofs. Six ignored, untracked stale
`__pycache__` directories under `engine/src/battle_engine/data/` were removed
as stale build output; no tracked file was affected.

## L. Verdict

**REMEDIATION COMPLETE — READY FOR NEW CANDIDATE COMMIT AND FULL PHASE F
REQUALIFICATION**

The blocked candidate `0dde69c9695c8c730fe190af23f6d92783072ffd` and every
artifact recorded in the Phase F report remain permanently **NOT APPROVED FOR
PUBLICATION**. That report was not modified. Complete Phase F requalification
must create fresh artifacts and hashes from the new committed SHA, and still
owes the outstanding gates it recorded: packaged GUI/first-user qualification,
the remaining standalone executable builds, installer lifecycle, independent
sdist installation, Linux qualification, and CI evidence for the replacement
SHA.
