# Bytefray V5 Alpha 1 — Phase F3

## Cross-Platform CI Remediation

Date: 2026-09-09. This is a narrow remediation record for the three defects
confirmed in
`docs/research/v5/V5_ALPHA1_PHASE_F_REQUALIFICATION_C280798.md`. Phase F
qualification was **not** resumed here, no installer/Linux/first-user work
was performed, and nothing was published. No feature work was done.

**REMEDIATION COMPLETE — READY FOR NEW CANDIDATE COMMIT, CI, AND FULL PHASE F
REQUALIFICATION**

## A. Starting baseline

| Property | Recorded value |
| --- | --- |
| Branch | `v5-research` |
| Starting HEAD SHA | `edc40baacd5dca3d736b62d4350bb6acd4073cad` (`docs(v5): record c280798 alpha1 qualification block`) |
| Local `origin/v5-research` | Same SHA |
| Blocked candidate | `c28079895ff6ba7faf84620e3c8f26ab4939a82a` |
| Blocked requalification report committed | Yes — confirmed at HEAD via `git show --stat HEAD`, 385 insertions, one file |
| Product version | `5.0.0a1` (`pyproject.toml:10`), unchanged throughout |
| Stable gameplay ruleset | `bytefray-rules-4`, unchanged throughout |
| Starting `git status --short` | Empty |
| Starting `git diff --check` | Empty |
| `.git/index.lock` | Absent |
| `.git/index` | 93,972 bytes, modified 2026-09-09 15:23 local — **unchanged in size and timestamp at the end of this phase** |
| Host | Windows 11 Pro, build 26120, AMD64 |
| Python (primary) | CPython 3.13.14 |
| Python (Defect C reproduction) | CPython 3.11.9, via the `py` launcher, in a disposable venv |
| Linux (Defect A reproduction) | WSL Ubuntu, CPython 3.12.3, in a disposable venv |
| Toolchain | pytest 9.1.1; Ruff 0.16.3; mypy 2.3.1 |

Note on the task's suggested starting SHA: the prompt named a candidate SHA
of `c280798`, matching the blocked report; the actual HEAD at the start of
this session was `edc40ba`, one commit ahead — the user had committed the
Phase F blocker report itself between sessions. This was confirmed (not
assumed) via `git show --stat HEAD` before any other action, per this
repository's git-durability protocol of re-verifying state rather than
trusting a value carried over from a prior turn.

## B. `c280798` blockers (recap)

From the requalification report, three causes made required CI (`ci.yml`)
red on every Linux job for candidate `c280798`:

- **C1** — `tools/packaging_data.is_python_bytecode()` not actually
  separator-agnostic on a POSIX host (new in that candidate's own Phase F2
  commit).
- **C2** — `test_v5_alpha1_phase_e_starter_refresh.py` reconstructing Phase C
  starter bytes via `git ls-tree`/`git cat-file` against historical commit
  `69fc958`, unreachable under GitHub Actions' shallow checkout (pre-existing).
- **C3** — a dataclass field with an unhashable `mappingproxy` default
  breaking module import under Python 3.11 (pre-existing; the requalification
  report, following the original blocked Phase F report's own wording,
  attributed this to `battle_engine.agent_api.MatchContextV2`).

This phase addresses all three. §G below records a correction found during
reproduction: C3's actual class was misidentified in both the original and
requalification reports.

## C. Defect A — reproduction, root cause, fix

**Reproduced before editing.** On this Windows host, both separator styles
already worked (`pathlib.Path` resolves to `WindowsPath`, which treats both
`/` and `\` as separators):

```text
'pkg/native.pyd' -> False   'pkg/agent.py' -> False   'pkg\data.bin' -> False
```

The exact CI-failing case, isolated to require *only* the directory-component
check (no bytecode suffix to also match) and run via WSL/Linux, reproduced
the defect precisely:

```text
$ wsl -e bash -c "... python3 -c \"...is_python_bytecode('__pycache__/stray.txt')...\""
fwd:  True
back: False   # __pycache__\stray.txt -- MISMATCH, the exact CI failure
```

**Root cause:** `is_python_bytecode()` built `Path(relative_path)` and
inspected `path.parts`. `pathlib.Path` resolves to the *host's* native
implementation — `PurePosixPath` behaviour on Linux, which does not treat
`\` as a separator — so a Windows-spelled relative path is one opaque
filename component on that host, not a `__pycache__` directory plus a file.
This is exactly backwards from what the F2 report claimed ("implemented with
pathlib" was presented as the fix *for* separator-agnosticism; it was
actually the cause of the remaining gap, because pathlib's own behaviour is
host-dependent).

**Fix** (`tools/packaging_data.py`): normalize `\` to `/` in the string
form of the input, then parse unconditionally with `PurePosixPath` — never
the host-default `Path` — so the answer no longer depends on which OS runs
the classifier:

```python
normalized = str(relative_path).replace("\\", "/")
path = PurePosixPath(normalized)
if any(part == CACHE_DIRECTORY_NAME for part in path.parts):
    return True
return path.suffix.lower() in BYTECODE_SUFFIXES
```

`.pyd` preservation is unaffected: it still has no bytecode suffix and no
`__pycache__` component, on either host.

## D. Defect A — cross-platform tests

Added directly to `engine/tests/test_frozen_bytecode_exclusion.py`'s
`REJECTED_PATHS`/`ALLOWED_PATHS` (so they run through the existing three
parametrized tests, each checked against an **expected value**, not merely
for agreement with a sibling spelling — a purely-internal-consistency check
would pass vacuously if both spellings were wrong the same way):

| Added, expected **rejected** | Added, expected **allowed** |
| --- | --- |
| `pkg\__pycache__\x.cpython-313.pyc` | `pkg\data.bin` |
| `pkg\__pycache__\readme.txt` (no bytecode suffix — isolates the directory-check path specifically) | `pkg\native.pyd` (also added forward-slash form) |
| `pkg\x.pyc` | |
| `pkg\x.pyo` | |

Full-module results, before vs. after the fix, same test file, same host:

| Host | Before fix | After fix |
| --- | --- | --- |
| Windows (CPython 3.13.14) | n/a — bug not observable on this host | **57 passed, 1 skipped** |
| Linux (WSL, CPython 3.12.3, disposable venv) | reproduced failure (§C) | **57 passed, 1 skipped** |

The one skip on both hosts is the frozen-artifact test gated on
`BYTEFRAY_FROZEN_EXE`, unset here by design (no frozen executable exists for
this in-progress candidate). Total module count rose from F2's 46 to 58
(12 new parametrized cases); 57 run and pass, 1 skips identically on both
platforms.

## E. Defect B — reproduction, root cause, fix

**Reproduced before editing:** `_seed_phase_c_starter()` in
`engine/tests/test_v5_alpha1_phase_e_starter_refresh.py` shelled out to
`git --no-optional-locks ls-tree -r --name-only 69fc958 <path>` and
`git cat-file -p 69fc958:<path>` to reconstruct the exact bytes V5 Alpha 1
Phase C bundled for each V5 starter. Its purpose, confirmed from source and
the module's own docstring: prove the `SUPERSEDED_STARTER_DIGESTS` allowlist
in `battle_engine.starters` really matches what that release shipped —
checked against real historical content, not against a hand-written fixture
that merely resembles it — so the upgrade-safety policy (missing → install
current; exact pristine predecessor → upgrade; current → no-op; customized →
preserve) is proven against genuine bytes.

This is unreachable under GitHub Actions' default shallow checkout
(`actions/checkout@v6`, `fetch-depth: 1`): commit `69fc958` is not present in
a depth-1 clone, so `git ls-tree` exits 128. Confirmed pre-existing (not
introduced by `c280798`): the F1 commit's own CI run failed identically,
before F2 existed.

**Fix policy:** per the task's explicit preference, this was **not** closed
by widening CI's `fetch-depth`. `git history is not a build or test
dependency` was made true rather than accommodated: the actual bytes commit
`69fc958` shipped for each of the four V5 starters were extracted once
(read-only `git cat-file`, no history depth requirement at *extraction*
time — the commit is fully reachable in a normal, non-shallow developer or
CI checkout of this session) and committed as an ordinary test fixture:

```text
engine/tests/fixtures/phase_c_v5_starters/
  v5_region_attacker/{agent.py,agent.yaml}
  v5_scout_striker/{agent.py,agent.yaml}
  v5_core_defender/{agent.py,agent.yaml}
  v5_dual_team/{agent.py,agent.yaml}
```

Each fixture's `starter_content_digest()` was verified to equal its
`SUPERSEDED_STARTER_DIGESTS` entry **exactly** before rewiring anything:

| Starter | Fixture digest | Matches allowlist |
| --- | --- | --- |
| `v5_region_attacker` | `f09d7fd5720e86b1a0f0c61de042a449bfba09e60065d92d894a24f8a44b6b00` | yes |
| `v5_scout_striker` | `2324bbf1ecebdca3149c16d3b9be94b6ec6bca409f6a78f0343f482c742f03cd` | yes |
| `v5_core_defender` | `be1ba8a24aee67fe378d0f90957d023024704697de7b4249d98122e75fac4e22` | yes |
| `v5_dual_team` | `2088e6b14d36ef2f0283ba11b9430c0eb0cddc4e8002ffeb0b372942ec3e29c0` | yes |

`_seed_phase_c_starter()` now copies from this fixture directory
(`shutil.copy2`) instead of invoking `git`. `subprocess` and `PHASE_C_COMMIT`'s
use as a live lookup key were removed; the constant is kept only as a
provenance comment. No production code (`battle_engine.starters`) changed —
`SUPERSEDED_STARTER_DIGESTS`/`CURRENT_STARTER_DIGESTS` are untouched, and the
four refresh-outcome semantics (missing/pristine/current/customized) are
exercised by the same test bodies as before, now fed from committed bytes.

## F. Shallow/archive test evidence (no Git history dependency)

Rather than only widen CI's checkout depth and call it proven, this was
tested directly: a location with **zero reachable git repository at all** —
strictly stronger than a shallow clone — containing only what the test needs
(the bundled `starter_agents` tree, the test file, and its new fixture
directory; no `.git` anywhere in the tree or any parent):

```text
$ cd <scratch>/no_git_min && git rev-parse --is-inside-work-tree
fatal: not a git repository (or any of the parent directories): .git
(exit 128)

$ python -m pytest -q --basetemp=.pytest-tmp engine/tests/test_v5_alpha1_phase_e_starter_refresh.py
24 passed in 4.83s
```

All 24 tests in the module pass with `git` itself unable to find a
repository, confirming the fix removed the dependency entirely rather than
merely tolerating a deeper shallow clone. (`--basetemp` was required only
because this scratch location has no `pytest.ini` of its own to set it —
unrelated to Defect B; the repository's own `pytest.ini` already sets this
for normal runs, see its comment about a stale, differently-ACL'd OS-default
temp directory on this host.)

**Full-history dependency removed: YES.**

## G. Defect C — Python 3.11 reproduction, root cause, fix

**Reproduced before editing, with an actual Python 3.11 interpreter**
(CPython 3.11.9, via the `py` launcher, disposable venv — not inferred, not
simulated):

```text
$ PYTHONPATH="engine/src;client/src" python3.11 -c "import battle_engine.match_service"
  File "...\battle_engine\match_service.py", line 72, in <module>
    @dataclass(frozen=True, init=False)
  File "...\dataclasses.py", line 815, in _get_field
    raise ValueError(f'mutable default {type(f.default)} for field '
ValueError: mutable default <class 'mappingproxy'> for field parameters is
not allowed: use default_factory
```

**Correction to the record.** Both the original blocked Phase F report and
this session's own requalification report named the affected class as
`MatchContextV2`. The actual traceback names `match_service.py:72`, which is
the `@dataclass(frozen=True, init=False)` decorator on **`MatchEntrant`**, a
different class in a different file. `agent_api.MatchContextV2` was checked
directly and already uses the correct `field(default_factory=lambda:
MappingProxyType({}))` form — it has no defect. This was caught by
reproducing against the real interpreter and the real traceback line number
rather than carrying the citation forward from the prior report, consistent
with this repository's standing rule that a prior audit's claims are
re-verified, not trusted. `MatchEntrant`'s `parameters` field has `init=False`
and a fully hand-written `__init__` that never reads the class-level default
(it always calls `object.__setattr__` itself) — but `dataclasses` still
inspects every field's default while processing the class regardless of
`init`, so the otherwise-inert bare default still raised.

**A second, previously undiscovered instance** of the identical pattern was
found by a codebase-wide search performed *after* fixing the first one, to
confirm no sibling instance remained: `app/services/designer_workflows.py`'s
`EntrantResultPresentation.parameters` had the same bare
`= MappingProxyType({})` default. `engine/tests/test_designer_workflows.py`
and five other files under `engine/tests/` (which **is** in `ci.yml`'s
default test path, unlike root `tests/`) import this module, so this second
instance would have broken the same required CI job on Python 3.11 even
after Defect C's first instance was fixed — it was not yet visible in the
`c280798` CI run only because Python module-execution stops at the first
class-definition error, and `MatchEntrant` is defined earlier in the import
graph.

**Fix**, identical minimal pattern in both files, matching the form already
proven correct elsewhere in this same codebase
(`NativeAgentResult.metadata`, `agent_api.MatchContextV2.parameters`):

```python
parameters: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
```

A codebase-wide search (`Mapping[...] = <bare value>` outside `field(...)`,
across `engine/src`, `client/src`, `app/`) found no third instance; the
remaining matches are module-level constants (not dataclass fields) or
already-correct `field(default_factory=...)` uses.

## H. Python-version evidence

| Interpreter | Import result |
| --- | --- |
| CPython 3.11.9 (`py -3.11`, disposable venv) | **Fails before fix** (both classes); **succeeds after** |
| CPython 3.13.14 (this repository's `.venv`) | Succeeds before and after — the defect was invisible on the primary dev interpreter |

`ci.yml`'s required matrix, read directly from the workflow file:
`['3.10', '3.11', '3.12', '3.13', '3.14']`, plus a separate non-blocking
`3.15-dev` job. Only 3.11 exhibited this failure; 3.10's mutable-default
check predates the 3.11 generalization (list/dict/set only) and does not
flag an unhashable-but-not-list/dict/set default, and 3.12–3.14 were not
independently re-verified beyond the primary 3.13 interpreter already in
daily use, consistent with the task's instruction not to claim results for
an interpreter not actually run.

## I. Semantic compatibility

| Check (Python 3.11, disposable venv, both fixed classes) | Result |
| --- | --- |
| Module imports | Succeeds |
| Construction without `parameters` (`MatchEntrant(...)`, `MatchEntrant.python(...)`) | Succeeds |
| Omitted parameters produce an empty mapping | `{}` |
| Independently constructed instances do not share mutable state | `e2.parameters is e1.parameters` → `False` (fresh `MappingProxyType` per instance, via `default_factory`) |
| Supplied parameters are accessible | `MatchEntrant.python(..., parameters={'k': 1})` → `{'k': 1}` |
| Mutation through the exposed mapping is rejected | `TypeError: 'mappingproxy' object does not support item assignment` |

No dataclass was made hashable; `frozen=True` (immutability of the dataclass
instance's own attributes) is unrelated to and was not conflated with
hashability of the *value* held in one field. Nothing about `MatchEntrant`'s
public construction signature, `agent_id`/`name` properties, or
`EntrantResultPresentation`'s fields changed.

## J. Focused validation

| Selection | Result |
| --- | --- |
| `test_frozen_bytecode_exclusion.py` (Windows) | 57 passed, 1 skipped |
| `test_frozen_bytecode_exclusion.py` (Linux, WSL) | 57 passed, 1 skipped |
| `test_v5_alpha1_phase_e_starter_refresh.py` | 24 passed |
| `test_v5_alpha1_phase_e_starter_refresh.py`, zero-git-history location (§F) | 24 passed |
| `test_windows_packaging_spec.py`, `test_v5_alpha1_phase_e_designer_services.py`, `test_native_match_service.py`, `test_v5_agent_parameters.py`, `test_v5_alpha1_phase_b_engine_hygiene.py`, `test_v4_stable_ruleset_equivalence.py`, `test_v5_starter_agents.py`, `test_agent_scaffold.py`, `test_frozen_scaffold_resources.py` (combined focused run, incl. both files above) | **414 passed, 7 skipped, 0 failed** |
| App-touched selection: `test_designer_workflows.py`, `test_v5_alpha1_phase_e_designer_services.py`, `test_evaluation_history_workflows.py`, `test_beta3_group_designer_workflows.py`, `test_cli_agent_listing.py`, `test_agent_workflows.py` (clean, isolated re-run — see §K note) | **108 passed** |
| Complete GUI/app selection (`-m gui tests client/tests/test_linux_pygame_smoke.py`) | **340 passed, 6 deselected** — identical to the pre-Phase-F3 baseline |

## K. Full validation

| Gate | Result |
| --- | --- |
| `python -m pytest` (full default suite, clean isolated run) | **3355 passed, 21 skipped, 3 deselected** in 372.76s |
| `ruff check .` | All checks passed |
| `mypy engine/src/battle_engine` | Success: no issues in 107 source files |
| `mypy client/src/battle_client` | Success: no issues in 16 source files |
| `mypy tools/packaging_data.py` | Success: no issues in 1 source file |

**Count reconciliation:** the requalification baseline was 3343 passed / 21
skipped / 3 deselected. Defect A's §D additions are the only test-count
change (+12 parametrized cases, all in `test_frozen_bytecode_exclusion.py`):
3343 + 12 = **3355**. Skipped (21) and deselected (3) are unchanged — Defect
B's fixture rewrite and Defect C's `default_factory` fix changed no test's
collection status, only what data backs already-existing tests.

**One contaminated run is recorded rather than hidden.** A first full-suite
run reported `1 failed, 3354 passed` — `test_agent_test.py::
test_canonical_artifacts_are_produced_and_replay_verifies` failed with
`FileNotFoundError` on a temp replay file. This was self-inflicted qualification-
harness contamination: a second, separate pytest invocation (the §J
app-touched selection) was started while the full suite was still running,
and both processes shared this repository's `--basetemp=.pytest-tmp`
(`pytest.ini`), colliding on temp-directory contents. Diagnosed by the
error's own path (`.pytest-tmp\test_canonical_artifacts_are_p0\...`,
mid-run, from a completely unrelated test module) and by the arithmetic
(3354 + 1 = 3355, the correct total either way). No repository file was
touched to produce or resolve this; the fix was running the two invocations
sequentially rather than concurrently. The clean re-run in §K's table is the
one with no concurrent qualification process running.

## L. CI status — still required

No commit was made in this phase (see §M), so **no new GitHub Actions run
exists for these changes** — claiming CI green from local simulation alone
would repeat exactly the error this remediation exists to fix. Local gates
(§J/§K) passed, including direct reproduction on a real Python 3.11
interpreter and a real Linux (WSL) host for the two platform/version-specific
defects, and the zero-git-history proof for the third. The next committed
candidate SHA must have its actual `ci.yml` run checked via `gh run list`
before any qualification claims about it, exactly as this phase and the
requalification phase before it checked `c280798`'s.

## M. Repository health

| Check | Result |
| --- | --- |
| `git --no-optional-locks status --short --untracked-files=all` | 5 modified, 8 untracked (the new fixture files) — listed below |
| `git --no-optional-locks diff --stat` | 5 files changed, 97 insertions(+), 46 deletions(-) |
| `git --no-optional-locks diff --check` | Empty except one informational CRLF-normalization note on `match_service.py` (no whitespace-error line reported) |
| `.git/index.lock` | Absent |
| `.git/index` | 93,972 bytes — **byte-identical to the starting value**, same modification timestamp |
| Git mutation commands run | **None** (`add`/`commit`/`push`/`pull`/`fetch`/`merge`/`rebase`/`reset`/`restore`/`checkout`/`switch`/`clean`/`stash`/`cherry-pick`/`worktree`/`tag`/`gc`/`prune` — none executed) |
| `git cat-file`/`git ls-tree` | Used read-only, twice: once to extract the Phase C fixture bytes (§E), once (implicitly, by the test itself) no longer at all after the fix |
| Disposable environments | One Python 3.11 venv, one WSL venv — both removed after use |
| Scratch directories | Two (`no_git_min`, and an abandoned full-repo `robocopy` copy stopped and removed before completion) — both removed |

Modified files: `app/services/designer_workflows.py`,
`engine/src/battle_engine/match_service.py`,
`engine/tests/test_frozen_bytecode_exclusion.py`,
`engine/tests/test_v5_alpha1_phase_e_starter_refresh.py`,
`tools/packaging_data.py`. Added (untracked): the eight
`engine/tests/fixtures/phase_c_v5_starters/**` files. Nothing deleted.

## N. Verdict

**REMEDIATION COMPLETE — READY FOR NEW CANDIDATE COMMIT, CI, AND FULL PHASE F
REQUALIFICATION**

Phase F qualification was not started here and must not be inferred from
this record. The next action is the user staging, committing, and pushing
this remediation (five modified files, eight new fixture files, this
report), producing a new candidate SHA, after which its actual `ci.yml` run
must be checked green on GitHub before qualification proceeds, and complete
Phase F qualification begins from the beginning against freshly built
artifacts from that new SHA.
