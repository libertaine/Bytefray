# Bytefray V5 Alpha 1 — Phase F Requalification

## Candidate `c280798` (post-F1/F2)

Date: 2026-09-09. This is a stopped release-qualification record for the
candidate that carries both the F1 and F2 packaging remediations. Product
source was not remediated here. This report supersedes nothing: the original
blocked Phase F report and the F1/F2 remediation records remain historical,
unedited evidence for their own candidates.

**ALPHA 1 PUBLICATION BLOCKED — REMEDIATION REQUIRED**

Required CI (`ci.yml`) is red on this exact candidate SHA across every Linux
Python version it tests. One of the three confirmed root causes is a
regression newly introduced by this candidate's own Phase F2 commit: the
packaging-hygiene helper's "separator-agnostic" bytecode filter is not
actually separator-agnostic on a POSIX host, contradicting the F2 remediation
report's own claim. This was confirmed against the live GitHub Actions run for
this SHA and independently reproduced locally via WSL. Per the task's
no-remediation instruction, qualification stopped here: no source, spec, test,
or CI file was edited, and no further packaging/installer/first-user work was
attempted once a candidate-introduced defect in required CI was confirmed.

## A. Candidate identity

| Property | Recorded value |
| --- | --- |
| Branch | `v5-research` |
| CANDIDATE_SOURCE_SHA | `c28079895ff6ba7faf84620e3c8f26ab4939a82a` |
| Commit subject | `fix(packaging): exclude bytecode from frozen artifacts` (Phase F2) |
| Commit time | 2026-09-09 14:08:07 -04:00 |
| Local `origin/v5-research` | Same SHA (no fetch performed; not required — remote already matched at session start and no fetch/pull/push ran) |
| Parent (F1) | `45ccc3462cf95686846bd6c4a2f5af31869c0cdb`, `fix(packaging): include API v2 scaffold resources`, 2026-09-09 13:12:11 -04:00 |
| Product version | `5.0.0a1` (`pyproject.toml:10`), unchanged throughout |
| Qualification start | 2026-09-09, this session |
| Host | Windows 11 Pro, build 26120, AMD64 |
| Python (source/build) | CPython 3.13.14 |
| Toolchain | pytest 9.1.1; Ruff 0.16.3; mypy 2.3.1; build 1.6.0; setuptools 84.0.0; wheel 0.48.0; PyInstaller 6.22.2 |
| GUI libraries in source/build environment | PySide6 6.11.2; pygame-ce 2.5.8 |
| WSL (used only for independent Linux reproduction, see §C) | Ubuntu, CPython 3.12.3 |

### Preconditions (Section 1 of the task)

| Check | Result |
| --- | --- |
| `git rev-parse HEAD` | `c28079895ff6ba7faf84620e3c8f26ab4939a82a` |
| `git rev-parse origin/v5-research` | Same SHA |
| `git status --short` | Empty |
| `git diff --check` | Empty |
| `.git/index.lock` | Absent |

All four preconditions passed before any further step. F1 and F2 were both
independently confirmed present in the exported tree (§B): `tools/packaging_data.py`
exists, `tools/bytefray.spec` references it, and all four scaffold template
directories (`agent_template`, `agent_template_annotated`, `agent_template_v2`,
`agent_template_v2_annotated`) exist under `engine/src/battle_engine/data`.

## B. Frozen qualification source

Per the task's execution adjustment, setup ran as separate, sequential
commands rather than one compound invocation:

1. `mkdir build/phase-f-c280798-20260909`
2. `mkdir build/phase-f-c280798-20260909/source`
3. `git --no-optional-locks archive --format=tar --output=build/phase-f-c280798-20260909/candidate-source.tar c28079895ff6ba7faf84620e3c8f26ab4939a82a` (read-only export; exit 0)
4. `tar -xf build/phase-f-c280798-20260909/candidate-source.tar -C build/phase-f-c280798-20260909/source` (separate command; exit 0)

No Git worktree was used. The archive's own SHA-256 is
`44b5e99ea8399407347b7fb7e28dc54b15a4771842c7a887b38b40198a2d98cc`. This root
did not previously exist (`phase-f-0dde69c-20260909`, `phase-f1-remediation`
and `phase-f2-*` are the only pre-existing `phase-f*` directories, all for
earlier candidates), so no stale qualification output was reused.

Wheel and sdist (§D) were built from this export. Source-level test/lint/type
gates (§E) ran against the live repository checkout rather than the export,
because the checkout was independently verified clean and byte-identical to
the candidate SHA immediately beforehand (§A) — the only risk the export
guards against (stray untracked/ignored files, e.g. `__pycache__`, leaking
into a build) does not apply to interpreted test/lint/type execution, only to
directory-collecting packaging steps, which is exactly why F1/F2 needed the
export/guard machinery they added. This distinction is recorded, not asserted
without support.

## C. Required CI audit — RED, three confirmed causes

Inspected via authenticated `gh` CLI against the live GitHub repository —
not inferred from workflow YAML alone, and not the historical claim in the
original Phase F report that "no remote CI status was queried."

`ci.yml` triggers on `[push, pull_request]` (unconditional — includes
`v5-research`). `linux-gui-smoke.yml` (push scoped to `main`),
`linux-package.yml` (push scoped to `v4-rc2-development`) and
`linux-pmars-build.yml` (push scoped to `main`) do not auto-trigger on this
branch and were not manually dispatched; no live status is claimed for them.

**`gh run list --branch v5-research`** shows the candidate's own CI run:

| Commit | Run | Conclusion |
| --- | --- | --- |
| `c280798` (this candidate) | `34387173926` | **failure**, 4m44s |
| `45ccc34` (F1) | `34381464848` | **failure**, 4m49s |
| `bfccd6a` | `34361692333` | failure |
| `0dde69c` (originally blocked candidate) | `34354817911` | failure |
| `3095b3d` | `34348985882` | failure |
| `69fc958` | `34342535751` | success |

CI has been red on `v5-research` since `3095b3d`, five commits before this
candidate. **This candidate's run failed on every Linux job**
(`test-linux-core` on Python 3.10, 3.11, 3.12, 3.14, and the non-blocking
3.15-dev job), each at the `Run core and headless tests` step.

Three distinct, independently confirmed root causes were found:

### C1. NEW — introduced by this candidate's own Phase F2 commit

`engine/tests/test_frozen_bytecode_exclusion.py::test_filter_agrees_across_windows_and_posix_separators[__pycache__/stray.txt]` fails on every Linux job:

```text
AssertionError: assert True == False
 +  where True = is_python_bytecode('__pycache__/stray.txt')
 +  and   False = is_python_bytecode('__pycache__\\stray.txt')
```

`tools/packaging_data.is_python_bytecode()` builds `Path(relative_path)` and
checks `path.parts` for a `__pycache__` component. `pathlib.Path` resolves to
`PurePosixPath`'s behavior on a POSIX host, which does **not** treat `\` as a
separator — so a backslash-spelled relative path is seen as one opaque
filename component, not a `__pycache__` directory plus a file. The F2
remediation report's own claim — *"Separator-agnostic: implemented with
`pathlib`, so `nested/__pycache__/x.pyc` and `nested\__pycache__\x.pyc` are
treated identically... on the very platform that ships these artifacts"* — is
therefore false when the function runs on Linux, which is exactly the
platform its own test asserts equivalence for and the platform this required
CI runs on.

**Independently reproduced outside CI**, via WSL (Ubuntu, CPython 3.12.3),
with no repository file modified:

```text
$ wsl -e bash -c "cd /mnt/d/Projects/BATTLE2 && python3 -c \"
import sys; sys.path.insert(0, 'tools')
from packaging_data import is_python_bytecode
print(is_python_bytecode('__pycache__/stray.txt'))
print(is_python_bytecode('__pycache__/stray.txt'.replace('/', chr(92))))
\""
True
False
```

This is a real, deterministic, platform-dependent defect in code this exact
candidate SHA added, not a flake and not inherited from an earlier commit —
the module did not exist before F2.

### C2. PRE-EXISTING — not introduced by this candidate

`engine/tests/test_v5_alpha1_phase_e_starter_refresh.py`'s helper
(`_seed_phase_c_starter`) shells out to
`git --no-optional-locks ls-tree -r --name-only 69fc958 <path>` to check
starter-digest provenance against history. It fails with exit 128 on every
Linux job:

```text
subprocess.CalledProcessError: Command '['git', '--no-optional-locks',
'ls-tree', '-r', '--name-only', '69fc958', ...]' returned non-zero exit
status 128.
```

`actions/checkout@v6`'s default `fetch-depth: 1` leaves historical commit
`69fc958` unreachable in the CI runner's shallow clone, so `git ls-tree`
cannot resolve it. **Confirmed pre-existing**: the F1 commit's own CI run
(`34381464848`) fails with the identical error, before F2's separator defect
existed. This is a test/CI-environment coupling gap (the checkout step never
fetches enough history for a test that reads it), not a defect in shipped
product code, and it is not part of F1/F2's remediation scope.

### C3. PRE-EXISTING — already-known limitation, newly connected to a CI break

On the Python 3.11 job specifically, test **collection** itself fails (exit
code 2, 23s total runtime, before any test runs):

```text
engine/src/battle_engine/match_service.py:72: in <module>
    @dataclass(frozen=True, init=False)
...
ValueError: mutable default <class 'mappingproxy'> for field parameters is
not allowed: use default_factory
```

Python 3.11 generalized dataclasses' mutable-default check from "is it a
`list`/`dict`/`set`" to "is it unhashable", and `MatchContextV2`'s `parameters`
field defaults to an unhashable `mappingproxy`. The original blocked Phase F
report already recorded this exact fact as a **known limitation** ("§O:
`MatchContextV2` contains an unhashable immutable mapping; no documented
hashability dependency was found") — but as a limitation, not as a confirmed
required-CI failure. This session is the first to connect it to an actual
required-CI break, because no prior session queried live CI status for this
branch. `ci.yml`'s own required matrix names Python 3.10–3.14, so a collection
failure on 3.11 is a required-gate failure, not an optional one.

**Disposition.** C1 is a material defect in this exact candidate's own new
code and independently reproduced outside CI; that alone satisfies the task's
"any material product/package defect" STOP condition. C2 and C3 are real and
also block a green required-CI signal, but predate this candidate and are not
part of F1/F2's claimed scope — they are reported for completeness, not as
new candidate regressions.

## D. Python artifacts

Built from the frozen export (§B), using the same frontend as prior phases:

```text
.venv\Scripts\python.exe -m build --no-isolation --outdir dist\phase-f-c280798-20260909\python
# cwd: build\phase-f-c280798-20260909\source
```

Build succeeded; no source edit or dependency change was needed.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `bytefray-5.0.0a1-py3-none-any.whl` | 970,136 | `a2543cb0ed37abf1a89441273ea034670477e4839cf0276cee76fd2462e7395f` |
| `bytefray-5.0.0a1.tar.gz` | 947,849 | `445f5599bc69decc3b942b3854cbf19e22ea6addecc40159d6b498f141fcc4e5` |

`tools/check_wheel.py` against the wheel: **passed**. Direct archive
inspection (wheel via `zipfile`, sdist via `tarfile`, script run against both):

| Property | Wheel | Sdist |
| --- | ---: | ---: |
| Members | 204 | 295 |
| `__pycache__`/`.pyc`/`.pyo` entries | **0** | **0** |
| `agent_template_v2/{agent.py,agent.yaml}` present | yes | yes |
| `agent_template_v2_annotated/{agent.py,agent.yaml}` present | yes | yes |

Wheel contains all 21 starter agent directories (6 V4 + 4 V5 + 11 legacy).
Both member counts match Phase F2's own recorded baseline (204/295) exactly.

## E. Source qualification (Windows, live checkout — verified clean and
byte-identical to the candidate SHA, §A/§B)

| Gate | Result |
| --- | --- |
| `ruff check .` | All checks passed |
| `mypy engine/src/battle_engine` | Success: no issues in 107 source files |
| `mypy client/src/battle_client` | Success: no issues in 16 source files |
| Focused source-gate selection (19 files, incl. both frozen-resource/bytecode-exclusion modules) | **580 passed, 7 skipped, 0 failed** |
| Full default headless suite (`pytest`) | **3343 passed, 21 skipped, 3 deselected** in 381.96s |
| Complete GUI/app selection (`-m gui tests client/tests/test_linux_pygame_smoke.py`) | **340 passed, 6 deselected** in 53.59s |

The full-suite and GUI-selection counts match Phase F2's own recorded
baseline (3343/21/3 and 340/6) exactly — no regression in gameplay, packaging
test, or GUI-test surface between the F2 remediation commit and this
identical candidate SHA. `BYTEFRAY_FROZEN_EXE` was not set for these runs
(no frozen executable exists yet for this candidate), so the frozen-artifact
tests skip by design, consistent with F1/F2's own documented baseline
behavior for an unset variable.

## F. Clean wheel environment qualification

A fresh venv (`build/phase-f-c280798-20260909/wheel-env`) had **only** the
built wheel installed (plus its declared `PyYAML>=6.0` dependency, resolved
from pip's local cache — no GUI extras). Import origin confirmed from that
venv's `Lib/site-packages`, not the repository. All commands ran with
`PYTHONPATH` unset and an isolated `BYTEFRAY_ROOT`.

| Check | Result |
| --- | --- |
| `--version` | `Bytefray 5.0.0a1, Agent API v2, result schema v1, replay schema v4` |
| Agent listing | 21 agents discovered |
| All 6 V4 starters (`v4_claimer`, `v4_concentrated_attacker`, `v4_defender_scout`, `v4_local_defender`, `v4_quorum`, `v4_scout`) | Present, resolved from site-packages |
| All 4 V5 starters (`v5_core_defender`, `v5_dual_team`, `v5_region_attacker`, `v5_scout_striker`) | Present, resolved from site-packages |
| Schema/preset delivery (`v5_region_attacker`) | `standard` → `attacker_reach=16`; `far_sighted` → `32` |
| Explicit override precedence | `far_sighted` (32) + `--a-param attacker_reach=24` → effective **24** |
| Invalid parameter rejection | `attacker_reach=9` (below declared minimum 10) → exit 1, `"9 is below the declared minimum 10"` |
| Stable match, omitted ruleset (`v4_scout` vs `v4_claimer`, seed 1234) | exit 0, `bytefray-rules-4`, winner A, score 1241/985 |
| Deterministic rerun (identical seed/settings, two independent invocations) | Replay files byte-identical, SHA-256 `878f9d1ae6cfa25bd410c5b3b066a90a9ca54f223936524bbc39d48ce03419c2` for both |
| API-v1 scaffold create | exit 0 |
| API-v2 scaffold create (blank + annotated) | exit 0 / exit 0 |
| API-v2 validate (blank + annotated) | exit 0 / exit 0, both `status: valid` |
| Result/replay/summary workflow | `result.json`, `summary.json`, replay `.jsonl` all produced; headless `replay --renderer headless` read them back (exit 0) |
| Headless operation | `PySide6` and `pygame` both confirmed absent from this venv |

Every check passed. This qualification is unaffected by the §C CI findings:
all three §C root causes are either POSIX-only pathlib behavior (C1, not
exercised by any of the above) or test-fixture git-history/Python-version
issues (C2/C3) that have no bearing on the built wheel's own behavior.

## G. Sdist qualification

A second, separate clean venv (`build/phase-f-c280798-20260909/sdist-env`)
installed **only** `bytefray-5.0.0a1.tar.gz` (PEP 517, default build
isolation — network available, no local source-tree dependency).

| Check | Result |
| --- | --- |
| Install | Succeeded; wheel built from the sdist internally by pip, then installed |
| Version | `Bytefray 5.0.0a1, Agent API v2, result schema v1, replay schema v4` |
| Import origin | That venv's `Lib/site-packages`, not the repository |
| V5 starter assets (all 4) | Present |
| API-v2 scaffold resources (both) | Present |
| Basic CLI/match workflow (`v4_scout` vs `v4_claimer`, seed 1234) | exit 0, winner A, score 1241/985 — identical to §F's wheel result |
| API-v2 create + validate | exit 0 / exit 0 |

Sdist qualification did **not** substitute for, and was not substituted by,
the wheel qualification in §F — both ran independently to completion.

## H. Sections not attempted — stopped per task §13

Once §C's C1 finding (a defect in this exact candidate's own new code,
independently reproduced outside CI) was confirmed, qualification stopped
per the task's explicit instruction: *"If ANY material product/package
defect is found: STOP. Do not fix it."* No source, spec, test, or CI file
was edited. The following were consequently **not attempted** for this
candidate — not attempted-and-failed, simply not started:

- Real end-to-end `tools/build_win.ps1` orchestration (Windows frozen
  executables, post-build hygiene guard, embedded GUI/agents-create smokes)
- Frozen-artifact hygiene/resource inventory proof for this SHA's own build
- Windows installer build and fresh/upgrade/customized-upgrade testing
- First-user packaged journey
- Documentation-driven authoring workflow (`docs/AGENT_API_V2.md`)
- Any Linux packaged qualification (WSL was used only for the read-only §C1
  reproduction — importing one module with no repository file changed — not
  for a Linux package build or install)

Nothing above is asserted to be either passing or failing for this candidate;
it is simply outside the evidence gathered before the stop.

## I. Repository health

| Check | Result |
| --- | --- |
| `git --no-optional-locks status --short` | Empty (this report is the only untracked addition) |
| `git --no-optional-locks rev-parse HEAD` | `c28079895ff6ba7faf84620e3c8f26ab4939a82a` — unchanged throughout |
| `git --no-optional-locks diff --check` | Empty |
| `.git/index.lock` | Absent |
| Git mutation commands run | **None** (`add`/`commit`/`push`/`pull`/`fetch`/`merge`/`rebase`/`reset`/`restore`/`checkout`/`switch`/`clean`/`stash`/`cherry-pick`/`worktree`/`tag` — none executed) |
| `git archive` | Used once, read-only, to populate `build/phase-f-c280798-20260909/source` |
| New artifacts | All under `build/phase-f-c280798-20260909/` and `dist/phase-f-c280798-20260909/`, both `.gitignore`-matched (`/build/`, `/dist/`); two disposable venvs and probe scratch directories are inside the same ignored root |
| WSL use | One read-only import/print, no repository file modified, no install performed inside WSL |

## J. Artifact inventory

| Type | Filename | Bytes | SHA-256 | Status |
| --- | --- | ---: | --- | --- |
| Wheel | `bytefray-5.0.0a1-py3-none-any.whl` | 970,136 | `a2543cb0ed37abf1a89441273ea034670477e4839cf0276cee76fd2462e7395f` | Built, checked, clean-installed, fully qualified (§D/§F) |
| Sdist | `bytefray-5.0.0a1.tar.gz` | 947,849 | `445f5599bc69decc3b942b3854cbf19e22ea6addecc40159d6b498f141fcc4e5` | Built, clean-installed, fully qualified (§D/§G) |
| Windows executables | Not built | — | — | Not attempted (§H) |
| Windows installer | Not built | — | — | Not attempted (§H) |

Python artifacts are under `dist/phase-f-c280798-20260909/python/`. No prior
candidate's artifacts (the blocked `0dde69c` build, or the F1/F2 remediation
proof builds) are reused, referenced, or overwritten by this row.

## K. Publication verdict

**ALPHA 1 PUBLICATION BLOCKED — REMEDIATION REQUIRED**

## L. Exact next action

Open a narrowly scoped remediation phase (Phase F3) addressing, at minimum:

1. **C1 (candidate regression, required):** make
   `tools/packaging_data.is_python_bytecode()` genuinely host-independent —
   e.g. normalize both separators (`str(relative_path).replace("\\", "/")`)
   before splitting into components, or check membership against a
   POSIX-normalized parts tuple, rather than relying on the host's default
   `pathlib.Path` implementation. Re-run
   `test_filter_agrees_across_windows_and_posix_separators` on both a Windows
   and a POSIX host (WSL is sufficient) before considering this closed.
2. **C2 (pre-existing, recommended alongside C1 since it also blocks a green
   signal):** either give `ci.yml`'s checkout step sufficient
   `fetch-depth` for `test_v5_alpha1_phase_e_starter_refresh.py`'s historical
   `git ls-tree` lookups, or make that test helper degrade gracefully when the
   referenced historical commit isn't reachable.
3. **C3 (pre-existing, recommended):** give `MatchContextV2.parameters` a
   `default_factory` (or otherwise avoid an unhashable dataclass default) so
   test collection succeeds on Python 3.11, one of `ci.yml`'s own required
   versions.

A source change to any of the above means a new candidate SHA and complete
Phase F requalification from the beginning, per the task's own rule that a
source change invalidates prior qualification evidence. The wheel and sdist
artifacts and their qualification in §F/§G remain valid *only* as evidence
that packaging-data correctness (API-v2 resources, starter assets, bytecode
exclusion) holds for `c280798`'s Python-packaging surface specifically — they
do not stand in for the blocked overall verdict above.
